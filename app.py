import io

import streamlit as st

from ai_edge_generator import generate_ai_edge_pattern
from vital_edge_generator import generate_vital_edge_pattern


st.set_page_config(
    page_title="Edge Art Generator",
    page_icon="◼",
    layout="centered",
)

st.title("Edge Art Generator")

st.write(
    "Generate a new branded pattern for the Edge franchise."
)

franchise = st.selectbox(
    "Franchise",
    [
        "AI Edge",
        "Vital Edge",
    ],
)

col1, col2 = st.columns(2)

with col1:
    width = st.number_input(
        "Width (px)",
        min_value=300,
        max_value=4000,
        value=1200,
        step=100,
    )

with col2:
    height = st.number_input(
        "Height (px)",
        min_value=300,
        max_value=4000,
        value=1600,
        step=100,
    )

if st.button(
    "Generate Pattern",
    use_container_width=True,
):

    with st.spinner(
        f"Generating {franchise} pattern..."
    ):

        if franchise == "AI Edge":
            image, metadata = generate_ai_edge_pattern(
                int(width),
                int(height),
            )
        else:
            image, metadata = generate_vital_edge_pattern(
                int(width),
                int(height),
            )

    st.image(
        image,
        caption=franchise,
        use_container_width=True,
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    filename = (
        "ai_edge_pattern.png"
        if franchise == "AI Edge"
        else "vital_edge_pattern.png"
    )

    st.download_button(
        label="Download PNG",
        data=buffer.getvalue(),
        file_name=filename,
        mime="image/png",
        use_container_width=True,
    )