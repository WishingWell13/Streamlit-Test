from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import fitz
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_image_annotation import detection

ANNOTATION_TITLE = "streamlit-image-annotation"


@st.cache_resource
def build_sample_pdf() -> Tuple[str, bytes]:
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "This sample PDF was generated at runtime so the demo works without checked-in binary files.\n\n"
        "Draw boxes around sections of the page, save them, and download the annotated file."
    )
    page.insert_text((72, 96), "Streamlit Image Annotation", fontsize=20, fontname="helv", color=(0, 0, 0))
    page.insert_text((72, 140), text, fontsize=12, fontname="helv", color=(0.1, 0.1, 0.1))

    table_rect = fitz.Rect(72, 220, 520, 360)
    page.draw_rect(table_rect, color=(0.2, 0.6, 0.86), width=2)
    page.insert_textbox(
        table_rect,
        "Try labelling this table area to see how annotations are written back into the PDF.",
        fontsize=11,
        align=fitz.TEXT_ALIGN_CENTER,
        fontname="helv",
    )

    note_rect = fitz.Rect(72, 380, 520, 460)
    page.draw_rect(note_rect, color=(0.9, 0.5, 0.1), width=2)
    page.insert_textbox(
        note_rect,
        "You can also upload your own PDF using the uploader above the canvas.",
        fontsize=11,
        align=fitz.TEXT_ALIGN_CENTER,
        fontname="helv",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return "sample-annotation.pdf", pdf_bytes


@dataclass
class PdfState:
    pdf_bytes: bytes | None
    pdf_name: str | None
    pdf_hash: str | None
    page_index: int
    annotations: Dict[int, List[dict]]


def get_state() -> PdfState:
    if "pdf_annotator" not in st.session_state:
        st.session_state.pdf_annotator = PdfState(
            pdf_bytes=None,
            pdf_name=None,
            pdf_hash=None,
            page_index=0,
            annotations={},
        )
    return st.session_state.pdf_annotator


def parse_labels(raw: str) -> List[str]:
    return [label.strip() for label in raw.split(",") if label.strip()]


def load_pdf_into_state(pdf_bytes: bytes, name: str) -> None:
    state = get_state()
    state.pdf_bytes = pdf_bytes
    state.pdf_name = name
    state.pdf_hash = hashlib.md5(pdf_bytes).hexdigest()
    state.page_index = 0
    state.annotations = {}


def page_to_image(pdf_bytes: bytes, page_index: int, zoom: float) -> Image.Image:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        mode = "RGB" if pix.n < 4 else "RGBA"
        image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        if mode == "RGBA":
            image = image.convert("RGB")
        return image
    finally:
        doc.close()


def save_temp_image(doc_hash: str, page_index: int, image: Image.Image) -> str:
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / f"streamlit_pdf_{doc_hash}_page_{page_index}.png"
    image.save(temp_path, format="PNG")
    return str(temp_path)


def ensure_page_index(state: PdfState, page_count: int) -> None:
    if state.page_index >= page_count:
        state.page_index = max(page_count - 1, 0)


def apply_annotations_to_pdf(pdf_bytes: bytes, annotations: Dict[int, List[dict]]) -> bytes:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page_index, page_annotations in annotations.items():
            if page_index >= doc.page_count:
                continue
            page = doc[page_index]
            # remove previous annotations created by this demo
            existing = []
            annot = page.first_annot
            while annot is not None:
                if (annot.info or {}).get("title") == ANNOTATION_TITLE:
                    existing.append(annot)
                annot = annot.next
            for annot in existing:
                page.delete_annot(annot)

            for item in page_annotations:
                x, y, width, height = item["bbox"]
                rect = fitz.Rect(x, y, x + width, y + height)
                pdf_annot = page.add_rect_annot(rect)
                pdf_annot.set_colors(stroke=(1, 0, 0))
                pdf_annot.set_border(width=1)
                pdf_annot.set_info(title=ANNOTATION_TITLE, content=item.get("label", ""))
                pdf_annot.update()
        return doc.tobytes()
    finally:
        doc.close()


st.title("📄 Annotate PDF pages with PyMuPDF")

st.write(
    """
    Upload a PDF (or load the bundled sample) to convert each page into an image, annotate it
    with `streamlit-image-annotation`, and write the bounding boxes back into the PDF using PyMuPDF.
    """
)

state = get_state()

uploaded_pdf = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_pdf is not None:
    load_pdf_into_state(uploaded_pdf.read(), uploaded_pdf.name)

col1, col2 = st.columns([2, 1])
with col1:
    st.caption("Need a quick test file? Load the included sample PDF.")
with col2:
    if st.button("Load sample PDF", use_container_width=True):
        sample_name, sample_bytes = build_sample_pdf()
        load_pdf_into_state(sample_bytes, sample_name)
        st.toast("Loaded sample PDF")

if state.pdf_bytes is None:
    st.info("Upload a PDF or load the sample to begin annotating.")
    st.stop()

with fitz.open(stream=state.pdf_bytes, filetype="pdf") as doc:
    page_count = doc.page_count

ensure_page_index(state, page_count)

st.subheader(f"Page {state.page_index + 1} of {page_count}")

navigation = st.columns([1, 1, 2])
with navigation[0]:
    if st.button("⬅️ Previous", disabled=state.page_index == 0, use_container_width=True):
        state.page_index = max(state.page_index - 1, 0)
        st.rerun()
with navigation[1]:
    if st.button("Next ➡️", disabled=state.page_index >= page_count - 1, use_container_width=True):
        state.page_index = min(state.page_index + 1, page_count - 1)
        st.rerun()
with navigation[2]:
    slider_value = st.slider(
        "Jump to page",
        min_value=1,
        max_value=page_count,
        value=state.page_index + 1,
        key="pdf_page_slider",
    )
    if slider_value - 1 != state.page_index:
        state.page_index = slider_value - 1
        st.rerun()

label_text = st.text_input(
    "Comma-separated label options",
    value="Paragraph, Figure, Table, Highlight",
)
label_options = parse_labels(label_text) or ["Annotation"]

zoom = st.slider(
    "Rendering zoom (1.0 = 72 DPI)",
    min_value=1.0,
    max_value=3.0,
    value=2.0,
    step=0.25,
    help="Higher zoom produces sharper images at the cost of processing time.",
)

display_width = st.slider("Canvas width", min_value=600, max_value=1200, value=900, step=50)
line_width = st.slider("Bounding-box border width", min_value=1.0, max_value=8.0, value=2.0)

page_image = page_to_image(state.pdf_bytes, state.page_index, zoom)
image_path = save_temp_image(state.pdf_hash or "temp", state.page_index, page_image)

existing_annotations = state.annotations.get(state.page_index, [])
if existing_annotations:
    bboxes = [item["bbox"] for item in existing_annotations]
    labels = [item["label_id"] for item in existing_annotations]
else:
    bboxes = None
    labels = None

annotations = detection(
    image_path=image_path,
    label_list=label_options,
    bboxes=bboxes,
    labels=labels,
    height=display_width,
    width=display_width,
    line_width=line_width,
    use_space=True,
    key=f"pdf-detection-{state.page_index}",
)

if annotations is not None:
    state.annotations[state.page_index] = annotations

st.divider()

st.subheader("Current page annotations")
current_annotations = state.annotations.get(state.page_index, [])
if current_annotations:
    table = [
        {
            "label": item["label"],
            "label_id": item["label_id"],
            "x": round(item["bbox"][0], 2),
            "y": round(item["bbox"][1], 2),
            "width": round(item["bbox"][2], 2),
            "height": round(item["bbox"][3], 2),
        }
        for item in current_annotations
    ]
    st.dataframe(pd.DataFrame(table))
else:
    st.info("Add a bounding box on this page to populate the table.")

if st.button("💾 Save annotations to PDF", type="primary", use_container_width=True):
    if not state.annotations:
        st.warning("Draw at least one bounding box before saving.")
    else:
        state.pdf_bytes = apply_annotations_to_pdf(state.pdf_bytes, state.annotations)
        st.toast("Annotations saved into the PDF.")
        st.rerun()

if state.annotations:
    st.caption(
        f"Tracking {sum(len(v) for v in state.annotations.values())} box(es) across"
        f" {len(state.annotations)} page(s)."
    )
else:
    st.caption("No annotations have been saved yet.")

st.download_button(
    "Download annotated PDF",
    data=state.pdf_bytes,
    file_name=(state.pdf_name or "annotated.pdf"),
    mime="application/pdf",
    use_container_width=True,
)
