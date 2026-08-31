import io

import streamlit as st

from ai_edge_generator import generate_ai_edge_pattern
from vital_edge_generator import generate_vital_edge_pattern

from production_vector import (
    generate_ai_edge_production_vector,
    generate_vital_edge_production_vector,
)


st.set_page_config(
    page_title="Edge Art Generator",
    page_icon="◼",
    layout="centered",
)

st.title(
    "Edge Art Generator"
)

st.write(
    "Generate a new branded pattern for the Edge franchise."
)


# ============================================================
# FRANCHISE
# ============================================================

franchise = st.selectbox(
    "Franchise",
    [
        "AI Edge",
        "Vital Edge",
    ],
)


# ============================================================
# SIZE
# ============================================================

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


# ============================================================
# GENERATE
# ============================================================

if st.button(
    "Generate Pattern",
    use_container_width=True,
):

    with st.spinner(
        f"Generating {franchise} pattern..."
    ):

        # ====================================================
        # PNG
        #
        # UNCHANGED EXISTING PILLOW GENERATOR
        # ====================================================

        if franchise == "AI Edge":

            image, metadata = (
                generate_ai_edge_pattern(
                    int(width),
                    int(height),
                )
            )

            png_filename = (
                "ai_edge_pattern.png"
            )

        else:

            image, metadata = (
                generate_vital_edge_pattern(
                    int(width),
                    int(height),
                )
            )

            png_filename = (
                "vital_edge_pattern.png"
            )


        # ====================================================
        # PRODUCTION VECTOR
        #
        # CLEAN VECTOR GENERATOR
        # ====================================================

        if franchise == "AI Edge":

            production_vector, vector_metadata = (
                generate_ai_edge_production_vector(
                    int(width),
                    int(height),
                )
            )

            vector_filename = (
                "ai_edge_production_vector.svg"
            )

        else:

            production_vector, vector_metadata = (
                generate_vital_edge_production_vector(
                    int(width),
                    int(height),
                )
            )

            vector_filename = (
                "vital_edge_production_vector.svg"
            )


    # ========================================================
    # PREVIEW
    # ========================================================

    st.image(
        image,
        caption=franchise,
        use_container_width=True,
    )


    # ========================================================
    # PNG
    # ========================================================

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


    # ========================================================
    # PRODUCTION VECTOR
    # ========================================================

    st.download_button(
        label="Download Production Vector",
        data=production_vector,
        file_name=vector_filename,
        mime="image/svg+xml",
        use_container_width=True,
    )