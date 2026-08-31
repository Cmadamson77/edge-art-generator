import io

import streamlit as st

from ai_edge_matched_export import (
    generate_ai_edge_matched,
)

from vital_edge_generator import (
    generate_vital_edge_pattern,
)

from production_vector import (
    generate_vital_edge_production_vector,
)


# ============================================================
# PAGE
# ============================================================

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
# DIMENSIONS
# ============================================================

col1, col2 = st.columns(
    2
)

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
        # AI EDGE
        #
        # PNG + PRODUCTION VECTOR ARE GENERATED FROM
        # THE SAME RANDOM SEED AND COMPOSITION.
        # ====================================================

        if franchise == "AI Edge":

            (
                image,
                metadata,
                production_vector,
                vector_metadata,
            ) = generate_ai_edge_matched(
                int(width),
                int(height),
            )

            seed = metadata[
                "seed"
            ]

            png_filename = (
                f"ai_edge_pattern_"
                f"{seed}.png"
            )

            vector_filename = (
                f"ai_edge_production_vector_"
                f"{seed}.svg"
            )

        # ====================================================
        # VITAL EDGE
        #
        # TEMPORARILY PRESERVES CURRENT GENERATORS.
        #
        # We will convert this to the same matched system
        # after validating AI Edge in Illustrator.
        # ====================================================

        else:

            image, metadata = (
                generate_vital_edge_pattern(
                    int(width),
                    int(height),
                )
            )

            (
                production_vector,
                vector_metadata,
            ) = (
                generate_vital_edge_production_vector(
                    int(width),
                    int(height),
                )
            )

            png_filename = (
                "vital_edge_pattern.png"
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
    # PNG BUFFER
    # ========================================================

    png_buffer = io.BytesIO()

    image.save(
        png_buffer,
        format="PNG",
    )


    # ========================================================
    # DOWNLOAD PNG
    # ========================================================

    st.download_button(
        label="Download PNG",
        data=png_buffer.getvalue(),
        file_name=png_filename,
        mime="image/png",
        use_container_width=True,
    )


    # ========================================================
    # DOWNLOAD PRODUCTION VECTOR
    # ========================================================

    st.download_button(
        label="Download Production Vector",
        data=production_vector,
        file_name=vector_filename,
        mime="image/svg+xml",
        use_container_width=True,
    )