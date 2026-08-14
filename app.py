import io

import streamlit as st

from ai_edge_generator import generate_ai_edge_pattern
from vital_edge_generator import generate_vital_edge_pattern
from ai_edge_svg import generate_ai_edge_svg
from vital_edge_svg import generate_vital_edge_svg


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

        # ----------------------------
        # PNG
        # ----------------------------

        if franchise == "AI Edge":
            image, metadata = generate_ai_edge_pattern(
                int(width),
                int(height),
            )

            png_filename = "ai_edge_pattern.png"

        else:
            image, metadata = generate_vital_edge_pattern(
                int(width),
                int(height),
            )

            png_filename = "vital_edge_pattern.png"

        # ----------------------------
        # SVG
        # ----------------------------

        if franchise == "AI Edge":
            svg_string, svg_metadata = generate_ai_edge_svg(
                int(width),
                int(height),
            )

            svg_filename = "ai_edge_pattern.svg"

        else:
            svg_string, svg_metadata = generate_vital_edge_svg(
                int(width),
                int(height),
            )

            svg_filename = "vital_edge_pattern.svg"

    # ----------------------------
    # Preview
    # ----------------------------

    st.image(
        image,
        caption=franchise,
        use_container_width=True,
    )

    # ----------------------------
    # PNG download
    # ----------------------------

    png_buffer = io.BytesIO()

    image.save(
        png_buffer,
        format="PNG",
    )

    st.download_button(
        label="Download PNG",
        data=png_buffer.getvalue(),
        file_name=png_filename,
        mime="image/png",
        use_container_width=True,
    )

    # ----------------------------
    # SVG download
    # ----------------------------

    st.download_button(
        label="Download SVG",
        data=svg_string,
        file_name=svg_filename,
        mime="image/svg+xml",
        use_container_width=True,
    )