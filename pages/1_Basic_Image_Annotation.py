import tempfile
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st
from streamlit_image_annotation import detection
from PIL import Image, ImageDraw, ImageFont

st.title("🧪 Basic image annotation")

st.write(
    """
    This page demonstrates the minimum wiring you need to start collecting bounding-box
    annotations from `streamlit-image-annotation`.
    """
)



@st.cache_resource
def build_sample_image() -> str:
    width, height = 960, 600
    image = Image.new("RGB", (width, height), "#f5f5f5")
    draw = ImageDraw.Draw(image)

    # Background panels
    draw.rectangle((40, 60, width - 40, height - 60), outline="#c3cad3", width=6)
    draw.rectangle((80, 120, width // 2, height - 100), fill="#d9e2f2")
    draw.rectangle((width // 2 + 20, 180, width - 80, height - 140), fill="#f7d9c4")

    draw.rounded_rectangle((120, 160, width // 2 - 40, 260), radius=12, fill="#3b5bdb")
    draw.rounded_rectangle((width // 2 + 60, 220, width - 120, 320), radius=12, fill="#37b24d")

    font = ImageFont.load_default()
    draw.text((140, 180), "Sample Workspace", font=font, fill="white")
    draw.text((width // 2 + 80, 240), "Annotate me!", font=font, fill="white")

    temp_path = Path(tempfile.gettempdir()) / "streamlit_image_annotation_sample.png"
    image.save(temp_path, format="PNG")
    return str(temp_path)

def parse_labels(raw: str) -> List[str]:
    labels = [label.strip() for label in raw.split(",")]
    return [label for label in labels if label]

label_text = st.text_input(
    "Comma-separated label options",
    value="Monitor, Keyboard, Plant, Mug",
    help="The component will show one color per label."
)
label_options = parse_labels(label_text) or ["Object"]

canvas_width = st.slider("Canvas width (pixels)", min_value=512, max_value=1024, value=768, step=64)
line_width = st.slider("Bounding-box border width", min_value=1.0, max_value=10.0, value=4.0)

st.caption("Use the toolbar above the image to switch tools, add labels, or delete boxes.")

annotations = detection(
    image_path=build_sample_image(),
    label_list=label_options,
    height=canvas_width,
    width=canvas_width,
    line_width=line_width,
    use_space=True,
    key="basic-detection",
)

st.divider()

st.subheader("What the component returns")
if annotations:
    records = [
        {
            "label": item["label"],
            "label_id": item["label_id"],
            "x": round(item["bbox"][0], 2),
            "y": round(item["bbox"][1], 2),
            "width": round(item["bbox"][2], 2),
            "height": round(item["bbox"][3], 2),
        }
        for item in annotations
    ]
    st.dataframe(pd.DataFrame.from_records(records))
else:
    st.info("Draw a bounding box on the image to see the coordinates and label metadata here.")

st.code(
    """
    [
        {'bbox': [x, y, width, height], 'label_id': 0, 'label': 'Monitor'},
        # ...
    ]
    """,
    language="python",
)
