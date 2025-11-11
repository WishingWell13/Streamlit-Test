import streamlit as st

st.set_page_config(
    page_title="Streamlit Image Annotation Demos",
    page_icon="🖼️",
    layout="wide",
)

st.title("Streamlit Image Annotation Demos")

st.write(
    """
    Explore how the [`streamlit-image-annotation`](https://pypi.org/project/streamlit-image-annotation/)
    component can help you collect bounding-box annotations directly inside Streamlit apps.
    Use the links below to jump into the interactive examples:
    """
)

pages = [
    {
        "path": "pages/1_Basic_Image_Annotation.py",
        "label": "Basic image annotation",
        "description": "Draw boxes on a sample image and inspect the coordinates and labels returned by the component.",
        "icon": "🧪",
    },
    {
        "path": "pages/2_PDF_Page_Annotation.py",
        "label": "PDF page-by-page annotation",
        "description": "Convert a PDF to images with PyMuPDF, annotate each page, and write the annotations back into the PDF.",
        "icon": "📄",
    },
]

for page in pages:
    st.page_link(
        page["path"],
        label=f"{page['icon']} {page['label']}",
        help=page["description"],
    )

st.divider()

st.subheader("Why two examples?")
st.markdown(
    """
    * **Basic image annotation** keeps things minimal so you can see the return format and
      learn how to validate bounding boxes.
    * **PDF annotation** shows how you can integrate the component into a more realistic workflow:
      extracting pages, iterating through them, and writing the annotations back into the PDF itself.
    """
)

st.info(
    """
    The examples generate their sample assets on the fly, so you can swap in your own files by
    editing the code or wiring up additional upload widgets.
    """
)
