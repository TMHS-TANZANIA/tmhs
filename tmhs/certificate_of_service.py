# Copyright (c) 2026, James Meshack and contributors
# For license information, please see license.txt
"""Certificate of Service, rendered from the branded SVG template.

There is no document behind this: the certificate is generated on demand from
an Employee record plus the director chosen in the download dialog, so nothing
is stored and nothing has to be kept in step with the employee's own fields.
"""

import base64
import glob
import io
import logging
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from functools import lru_cache

import frappe
from fontTools import subset
from fontTools.ttLib import TTFont
from frappe import _
from frappe.utils import getdate

SVG_NS = "http://www.w3.org/2000/svg"
TEMPLATE = os.path.join(os.path.dirname(__file__), "certificate_of_service.svg")

# Only these may produce a certificate. Enforced server-side as well as in the
# form script, since the download endpoint is reachable directly by URL.
PRINT_ROLES = ("HR Manager", "HR User")

# viewBox is "0 0 1122.5601 793.91998" — A4 landscape (297x210mm) at 96dpi.
PAGE_WIDTH = 1122.5601

# The certificate has two centred columns of text. The body lines sit on the
# page centre, which is also the centre of the rule under the employee's name.
CENTRE = PAGE_WIDTH / 2

# The director's name and title sit centred under the left-hand signature rule,
# which the artwork draws (as a filled path inside a clipped group, so there is
# no tidy attribute to read it off) from x=159 to x=335.
SIGNATURE = 247.0

# The template names its fonts but cannot carry them, so anyone opening the
# certificate without Neue Haas Grotesk / Century installed gets a fallback
# face — wrong on a document that is company branding, and wide enough here to
# make the body line overlap itself. These get embedded as @font-face so the
# file is self-contained. Subset to Latin-1 first: the full faces would add
# ~1.4MB to every certificate, the subset WOFFs add ~126KB.
FONT_DIR = os.path.join(os.path.dirname(__file__), "public", "fonts")
FONT_SOURCES = {
	"Neue Haas Grotesk Display Pro": "neue-haas-grotesk-display-pro-cufonfonts/NeueHaasDisplay*.ttf",
	"Century": "century/Century *.ttf",
}

CSS_WEIGHTS = {"normal": 400, "bold": 700}

CHARSET = "".join(chr(c) for c in range(0x20, 0x7F)) + "".join(chr(c) for c in range(0xA0, 0x100))

ET.register_namespace("", SVG_NS)


@lru_cache(maxsize=1)
def _faces():
	"""family -> {usWeightClass: path} for the upright faces on disk.

	The weight is read out of each font's OS/2 table rather than inferred from
	its filename. This release numbers its faces a grade heavier than they are
	named — Thin=300, Light=400, Roman=500, Medium=600 — and fontconfig matches
	on usWeightClass, so trusting the names would embed faces one grade bolder
	than a desktop renderer picks from the same template.
	"""
	faces = {}
	for family, pattern in FONT_SOURCES.items():
		faces[family] = {
			TTFont(path, lazy=True)["OS/2"].usWeightClass: path
			for path in sorted(glob.glob(os.path.join(FONT_DIR, pattern)))
			if "Italic" not in os.path.basename(path)
		}
	return faces


def _face_for(family, weight):
	by_weight = _faces()[family]
	want = int(CSS_WEIGHTS.get(weight, weight))
	return by_weight.get(want) or by_weight[min(by_weight, key=lambda w: (abs(w - want), w))]


def _template_fonts(root):
	"""The (family, font-weight) pairs the template actually asks for."""
	pairs = set()
	for el in root.iter(f"{{{SVG_NS}}}text"):
		style = el[0].get("style") or ""
		if family := re.search(r"font-family:'?([^;']+)", style):
			weight = re.search(r"font-weight:([^;]+)", style)
			pairs.add((family.group(1), weight.group(1) if weight else "normal"))
	return tuple(sorted(pairs))


@lru_cache(maxsize=1)
def _font_face_css(pairs):
	"""Latin-1 subsets of the brand faces, inline, as @font-face rules."""
	logging.getLogger("fontTools").setLevel(logging.ERROR)  # "FFTM NOT subset" chatter

	rules = []
	for family, weight in pairs:
		font = TTFont(_face_for(family, weight))
		options = subset.Options()
		options.layout_features = ["*"]
		subsetter = subset.Subsetter(options=options)
		subsetter.populate(text=CHARSET)
		subsetter.subset(font)

		buf = io.BytesIO()
		font.flavor = "woff"
		font.save(buf)
		data = base64.b64encode(buf.getvalue()).decode()
		rules.append(
			f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{weight};"
			f"src:url(data:font/woff;base64,{data}) format('woff')}}"
		)
	return "\n".join(rules)


def _ordinal(day):
	return "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def _long_date(value):
	d = getdate(value)
	return f"{d.day}{_ordinal(d.day)} {d.strftime('%B')}, {d.year}"


def _tracking(tspan):
	"""The letter-spacing the template baked in as a per-glyph `dx` array.

	The PDF export wrote one `dx` per glyph, all but the kerning outliers
	sharing a single value — the company's tracking. Replacing the text drops
	that array, so the value is read back here and re-applied as uniform
	letter-spacing; without it those lines render visibly tighter than the
	template.

	Zeros are excluded because Inkscape leaves a run of them where a line was
	re-edited by hand, but the mode still has to cover a third of the glyphs:
	on a line that carries no tracking at all the only non-zero entries are one
	or two kerning pairs, and applying those to every glyph would be wrong.
	"""
	dx = (tspan.get("dx") or "").split()
	nonzero = [v for v in dx if float(v)]
	if not nonzero:
		return None
	value, count = Counter(nonzero).most_common(1)[0]
	return value if count * 3 >= len(dx) else None


def _set_text(root, node_id, value, x):
	"""Replace a template placeholder with `value`, centred on `x`.

	The template came out of Inkscape as one <tspan> per line. The whole tspan
	is rebuilt: same style (so font family, weight and size are preserved
	verbatim), tracking restored via letter-spacing, and text-anchor:middle so
	the renderer does the width maths for us.

	Most lines are positioned by a `transform="matrix(s,0,0,s,tx,ty)"` with the
	text itself at x=0, so the anchor point is the matrix translation and `x`
	has to be written there; the few lines Inkscape rewrote carry a plain x/y
	in page coordinates instead.
	"""
	el = root.find(f".//{{{SVG_NS}}}text[@id='{node_id}']")
	if el is None:
		frappe.throw(_("Certificate template is missing node {0}").format(node_id))

	tspan = el[0]
	style = tspan.get("style", "")
	if track := _tracking(tspan):
		style = f"{style};letter-spacing:{track}px"

	matrix = re.match(
		r"matrix\(([\d.-]+,[\d.-]+,[\d.-]+,[\d.-]+),[\d.-]+,([\d.-]+)\)", el.get("transform") or ""
	)
	if matrix:
		scale, ty = matrix.groups()
		transform, local_x, y = f"matrix({scale},{x},{ty})", "0", "0"
	else:
		transform, local_x, y = None, str(x), el.get("y")

	el.clear()
	el.set("id", node_id)
	el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
	el.set("x", local_x)
	el.set("y", y)
	el.set("style", f"{style};text-anchor:middle")
	if transform:
		el.set("transform", transform)

	child = ET.SubElement(el, f"{{{SVG_NS}}}tspan")
	child.set("id", f"tspan{node_id[4:]}")
	child.set("x", local_x)
	child.set("y", y)
	child.set("style", style)
	child.text = " ".join(value.split())


def _director_name(user):
	"""Printed name of the director signing the certificate.

	Their Employee record is preferred over the User's full name: it is the
	spelling HR maintains, and it is what the employee's own name on the
	certificate comes from. The title cannot come from there — most users have
	no Employee link — so it is supplied by the download dialog.
	"""
	return (
		frappe.db.get_value("Employee", {"user_id": user}, "employee_name")
		or frappe.utils.get_fullname(user)
		or user
	)


@frappe.whitelist()
def service_period(employee):
	"""Dates the download dialog starts from, both editable there.

	The certificate states the period served, which is the contract's, not the
	employee record's: Date of Joining is only a fallback for someone hired
	before any of this was in the system.
	"""
	frappe.only_for(PRINT_ROLES)

	doc = frappe.get_doc("Employee", employee)
	doc.check_permission("read")

	# The latest contract wins: an employee who has been renewed has several,
	# and the current one is what the certificate is being issued against.
	contract = (
		frappe.db.get_value(
			"Contract",
			{"party_type": "Employee", "party_name": employee},
			["start_date", "end_date"],
			as_dict=True,
			order_by="start_date desc",
		)
		or frappe._dict()
	)
	offer_date = doc.job_applicant and frappe.db.get_value(
		"Job Offer", {"job_applicant": doc.job_applicant}, "offer_date", order_by="offer_date desc"
	)

	return {
		"from_date": offer_date or contract.start_date or doc.date_of_joining,
		"to_date": contract.end_date or doc.contract_end_date or doc.relieving_date,
	}


def render_svg(employee, from_date, to_date, director_name, director_title):
	"""Fill the template. Everything here is verified in the form script, which
	can name the field and the record to fix, so nothing throws."""
	tree = ET.parse(TEMPLATE)
	root = tree.getroot()

	style = ET.Element(f"{{{SVG_NS}}}style")
	style.set("type", "text/css")
	style.text = _font_face_css(_template_fonts(root))
	root.insert(0, style)

	for node_id, value, x in (
		("text367", employee.employee_name.upper(), CENTRE),
		(
			"text368",
			f"has been working with us in the position of {employee.designation} "
			f"from {_long_date(from_date)} to",
			CENTRE,
		),
		("text369", _long_date(to_date), CENTRE),
		("text370", director_name.upper(), SIGNATURE),
		("text371", director_title, SIGNATURE),
	):
		_set_text(root, node_id, value, x)

	return ET.tostring(root, encoding="unicode", xml_declaration=True)


def render_pdf(employee, from_date, to_date, director_name, director_title):
	"""The same SVG, converted by headless Chrome.

	Not Frappe's own wkhtmltopdf: its QtWebKit rasterises the whole page to a
	single ~74dpi JPEG, which is not printable as a certificate. Chrome keeps
	the artwork vector and subsets the @font-face brand fonts into the PDF, so
	it prints correctly on a machine that has neither font installed.
	"""
	html = (
		"<html><head><meta charset='utf-8'><style>"
		"@page{size:297mm 210mm;margin:0}"
		"html,body{margin:0;padding:0}"
		"svg{display:block;width:297mm;height:210mm}"
		"</style></head><body>"
		+ render_svg(employee, from_date, to_date, director_name, director_title).split("?>", 1)[-1]
		+ "</body></html>"
	)

	with tempfile.TemporaryDirectory() as tmp:
		source = os.path.join(tmp, "certificate.html")
		target = os.path.join(tmp, "certificate.pdf")
		with open(source, "w") as f:
			f.write(html)

		command = [
			_chrome(),
			"--headless=new",
			"--disable-gpu",
			f"--user-data-dir={tmp}",  # Chrome needs somewhere writable
			"--no-pdf-header-footer",
			f"--print-to-pdf={target}",
		]
		if os.geteuid() == 0:
			# Chrome's sandbox refuses to start as root, which is how bench
			# runs inside most containers. The only page ever loaded is the
			# file we just wrote, so there is no untrusted content to sandbox.
			command.insert(1, "--no-sandbox")
		command.append(f"file://{source}")

		try:
			# HOME is often unset or unwritable under supervisor; Chrome fails
			# at startup without one it can write to.
			subprocess.run(
				command,
				check=True,
				capture_output=True,
				timeout=120,
				env={**os.environ, "HOME": tmp},
			)
		except subprocess.CalledProcessError as e:
			frappe.throw(_("PDF conversion failed: {0}").format(e.stderr.decode()[-500:]))
		except subprocess.TimeoutExpired:
			frappe.throw(_("PDF conversion timed out."))

		with open(target, "rb") as f:
			return f.read()


# Absolute paths are probed as well as PATH: bench workers run under supervisor
# with a trimmed PATH that usually excludes /snap/bin, so an installed Chrome can
# still be invisible to shutil.which() even though it works in an admin's shell.
CHROME_NAMES = ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser", "chrome")
CHROME_PATHS = (
	"/usr/bin/google-chrome-stable",
	"/usr/bin/google-chrome",
	"/usr/bin/chromium",
	"/usr/bin/chromium-browser",
	"/snap/bin/chromium",
	"/opt/google/chrome/chrome",
)


def _chrome():
	"""Path to a Chrome/Chromium binary, or a throw explaining how to supply one."""
	try:
		configured = frappe.conf.get("chrome_binary")
	except RuntimeError:
		configured = None  # no site bound, e.g. the offline self-check

	if configured:
		if os.access(configured, os.X_OK):
			return configured
		frappe.throw(_("chrome_binary is set to {0} but that is not an executable file.").format(configured))

	for name in CHROME_NAMES:
		if path := shutil.which(name):
			return path
	for path in CHROME_PATHS:
		if os.access(path, os.X_OK):
			return path

	frappe.throw(
		_(
			"No Chrome or Chromium binary found — one is required to produce the PDF. "
			"Install it on the server (for example: sudo apt install -y chromium), "
			'or add "chrome_binary": "/full/path/to/chrome" to site_config.json.'
		)
	)


@frappe.whitelist()
def download(employee, director, title, from_date, to_date):
	frappe.only_for(PRINT_ROLES)

	doc = frappe.get_doc("Employee", employee)
	doc.check_permission("read")

	frappe.response.filename = f"Certificate of Service - {doc.employee_name}.pdf"
	frappe.response.filecontent = render_pdf(doc, from_date, to_date, _director_name(director), title)
	frappe.response.type = "download"
