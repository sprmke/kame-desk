from html.parser import HTMLParser
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph

_HEADING_SIZES = {"h1": 14, "h2": 12, "h3": 11}


def _looks_like_html(body: str) -> bool:
    stripped = body.lstrip().lower()
    return stripped.startswith(("<p", "<h1", "<h2", "<h3", "<ul", "<ol", "<div", "<blockquote"))


class _HtmlBlocks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self._kind = "p"
        self._buf: list[str] = []
        self._in_ol = False
        self._ol_index = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("p", "h1", "h2", "h3", "blockquote"):
            self._flush()
            self._kind = tag
        elif tag == "br":
            self._buf.append("<br/>")
        elif tag in ("strong", "b"):
            self._buf.append("<b>")
        elif tag in ("em", "i"):
            self._buf.append("<i>")
        elif tag == "u":
            self._buf.append("<u>")
        elif tag in ("s", "strike"):
            self._buf.append("<strike>")
        elif tag == "ul":
            self._flush()
            self._in_ol = False
        elif tag == "ol":
            self._flush()
            self._in_ol = True
            self._ol_index = 0
        elif tag == "li":
            self._flush()
            self._kind = "li"
            if self._in_ol:
                self._ol_index += 1
        elif tag == "a":
            self._buf.append("<u>")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("p", "h1", "h2", "h3", "blockquote", "li"):
            self._flush()
            self._kind = "p"
        elif tag in ("strong", "b"):
            self._buf.append("</b>")
        elif tag in ("em", "i"):
            self._buf.append("</i>")
        elif tag == "u":
            self._buf.append("</u>")
        elif tag in ("s", "strike"):
            self._buf.append("</strike>")
        elif tag == "a":
            self._buf.append("</u>")
        elif tag in ("ul", "ol"):
            self._in_ol = False
            self._flush()

    def handle_data(self, data: str) -> None:
        self._buf.append(escape(data))

    def _flush(self) -> None:
        xml = "".join(self._buf).strip()
        self._buf = []
        if not xml:
            return
        kind = self._kind
        if kind == "li":
            prefix = f"{self._ol_index}. " if self._in_ol else "• "
            xml = prefix + xml
        self.blocks.append((kind, xml))


def html_body_to_blocks(body: str) -> list[tuple[str, str]]:
    if not _looks_like_html(body):
        return [("p", escape(line)) for line in body.splitlines()]
    parser = _HtmlBlocks()
    parser.feed(body)
    parser.close()
    parser._flush()
    return parser.blocks or [("p", "")]


def render_document_pdf(
    clinic_name: str,
    title: str,
    body: str,
    *,
    signed: bool = False,
    brand_color: str | None = None,
) -> bytes:
    from reportlab.pdfgen import canvas

    from app.services.pdf_brand import draw_letterhead_accent

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, clinic_name)
    y -= 0.12 * inch
    draw_letterhead_accent(c, inch, y, width - 2 * inch, brand_color)
    y -= 0.18 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y, title)
    y -= 0.28 * inch

    body_width = width - 2 * inch
    blocks = html_body_to_blocks(body)

    def style_for(kind: str) -> ParagraphStyle:
        if kind in _HEADING_SIZES:
            return ParagraphStyle(
                kind,
                fontName="Helvetica-Bold",
                fontSize=_HEADING_SIZES[kind],
                leading=_HEADING_SIZES[kind] + 4,
            )
        if kind == "blockquote":
            return ParagraphStyle(
                "quote",
                fontName="Helvetica-Oblique",
                fontSize=10,
                leading=14,
                leftIndent=12,
            )
        return ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
        )

    for kind, xml in blocks:
        para = Paragraph(xml or "&nbsp;", style_for(kind))
        _w, h = para.wrap(body_width, height)
        if y - h < inch:
            c.showPage()
            y = height - inch
        para.drawOn(c, inch, y - h)
        y -= h + 6

    y -= 0.2 * inch
    if y < inch:
        c.showPage()
        y = height - inch
    c.setFont("Helvetica", 10)
    if signed:
        c.drawString(inch, y, "Signed electronically")
    else:
        c.drawString(inch, y, "Signature: _________________________")

    c.showPage()
    c.save()
    return buffer.getvalue()
