# Copyright (c) 2026, James Meshack and contributors
# For license information, please see license.txt
"""Self-check for the certificate renderer. No site needed. From apps/tmhs:

    ../../env/bin/python -m tmhs.test_certificate_of_service

(as a module, not a path: running the file directly puts tmhs/ on sys.path,
where the tmhs/tmhs/ module folder shadows the app package.)
"""

import io
import os
import re
import shutil
import xml.etree.ElementTree as ET
from types import SimpleNamespace

from pypdf import PdfReader

from tmhs.certificate_of_service import (
	CENTRE,
	SIGNATURE,
	SVG_NS,
	TEMPLATE,
	_face_for,
	_ordinal,
	_template_fonts,
	render_pdf,
	render_svg,
)

EMPLOYEE = SimpleNamespace(
	name="HR-EMP-00042",
	employee_name="Amina Said Hamis",
	designation="Waste Attendant",
)
PERIOD = ("2025-01-03", "2026-03-30")
DIRECTOR = ("Victoria Wilbard", "Director of HR & Administration")


def check():
	svg = render_svg(EMPLOYEE, *PERIOD, *DIRECTOR)
	root = ET.fromstring(svg)

	def where(el):
		"""The x the line is centred on, in page coordinates.

		Lines carrying a transform sit at x=0 inside it, so the anchor is the
		matrix translation; the rest carry a plain page x.
		"""
		matrix = re.match(r"matrix\([\d.-]+,[\d.-]+,[\d.-]+,[\d.-]+,([\d.-]+),", el.get("transform") or "")
		return round(float(matrix.group(1) if matrix else el.get("x")), 5)

	got = {
		el.get("id"): ("".join(el.itertext()), el.get("style").rsplit("text-anchor:", 1)[-1], where(el))
		for el in root.iter(f"{{{SVG_NS}}}text")
		if "text-anchor" in (el.get("style") or "")
	}

	# body lines, centred on the page
	assert got["text367"] == ("AMINA SAID HAMIS", "middle", round(CENTRE, 5)), got["text367"]
	assert got["text368"] == (
		"has been working with us in the position of Waste Attendant from 3rd January, 2025 to",
		"middle",
		round(CENTRE, 5),
	), got["text368"]
	assert got["text369"] == ("30th March, 2026", "middle", round(CENTRE, 5)), got["text369"]

	# signature block, centred on the left-hand rule
	assert got["text370"] == ("VICTORIA WILBARD", "middle", SIGNATURE), got["text370"]
	assert got["text371"] == ("Director of HR & Administration", "middle", SIGNATURE), got["text371"]

	# ordinals, including the teens that do not follow the last-digit rule
	assert [_ordinal(d) for d in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 30)] == [
		"st", "nd", "rd", "th", "th", "th", "th", "st", "nd", "rd", "th"
	]

	# untouched template lines keep their original anchors
	assert "text-anchor" not in ET.tostring(root.find(f".//{{{SVG_NS}}}text[@id='text366']"), "unicode")

	# branding is preserved verbatim: same font family/weight/size as the template
	tpl = {el.get("id"): el[0].get("style") for el in ET.parse(TEMPLATE).getroot().iter(f"{{{SVG_NS}}}text")}
	for node_id in got:
		out = root.find(f".//{{{SVG_NS}}}text[@id='{node_id}']")[0].get("style")
		for prop in ("font-family", "font-weight", "font-size", "font-variant", "fill"):
			want = re.search(rf"(?:^|;){prop}:[^;]*", tpl[node_id])
			assert want and want.group() in f";{out}", (node_id, prop, out)

	# the template's tracking, baked in as a per-glyph dx array, is re-applied
	# as uniform letter-spacing. text367 carries only a kerning pair, not
	# tracking, and must come out with none.
	spacing = {
		node_id: (
			re.search(r"letter-spacing:([\d.]+)px", root.find(f".//{{{SVG_NS}}}text[@id='{node_id}']").get("style"))
			or [None, None]
		)[1]
		for node_id in got
	}
	assert spacing == {
		"text367": None,
		"text368": "1.6",  # 0.1 x 16
		"text369": "1.6",
		"text370": "1.2",  # 0.1 x 12
		"text371": "1.6",
	}, spacing

	# every family/weight the template uses is embedded, so the file renders
	# correctly on a machine with no brand fonts installed
	pairs = _template_fonts(ET.parse(TEMPLATE).getroot())
	css = root.find(f"{{{SVG_NS}}}style").text
	for family, weight in pairs:
		assert f"font-family:'{family}';font-style:normal;font-weight:{weight};" in css, (family, weight)
	assert css.count("data:font/woff;base64,") == len(pairs)

	# each face is the one fontconfig would pick. Matched on the font's own
	# usWeightClass — this release's filenames are a grade lighter than its
	# actual weights (Light=400, Roman=500, Medium=600).
	assert {p: os.path.basename(_face_for(*p)) for p in pairs} == {
		("Century", "normal"): "Century Normal.ttf",
		("Neue Haas Grotesk Display Pro", "300"): "NeueHaasDisplayThin.ttf",
		("Neue Haas Grotesk Display Pro", "500"): "NeueHaasDisplayRoman.ttf",
		("Neue Haas Grotesk Display Pro", "600"): "NeueHaasDisplayMediu.ttf",
		("Neue Haas Grotesk Display Pro", "normal"): "NeueHaasDisplayLight.ttf",
	}

	# PDF must stay vector with the brand fonts subsetted in. Worth asserting:
	# Frappe's own wkhtmltopdf silently rasterises this page to a single ~74dpi
	# JPEG with zero embedded fonts, and that failure is invisible by eye.
	if not any(shutil.which(b) for b in ("google-chrome", "chromium", "chromium-browser")):
		print("ok (PDF check skipped: no Chrome on this machine)")
		return

	page = PdfReader(io.BytesIO(render_pdf(EMPLOYEE, *PERIOD, *DIRECTOR))).pages[0]
	assert 296.5 < float(page.mediabox.width) / 72 * 25.4 < 297.5, page.mediabox
	assert 209.5 < float(page.mediabox.height) / 72 * 25.4 < 210.5, page.mediabox

	embedded = {
		str(f.get_object()["/BaseFont"]).split("+")[-1]
		for f in page["/Resources"]["/Font"].get_object().values()
	}
	assert embedded == {
		"Century-Normal",
		"NeueHaasDisplay-Thin",
		"NeueHaasDisplay-Light",
		"NeueHaasDisplay-Roman",
		"NeueHaasDisplay-Mediu",
	}, embedded
	assert "AMINA SAID HAMIS" in (page.extract_text() or ""), "text was rasterised"

	print("ok")


if __name__ == "__main__":
	check()
