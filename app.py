# ============================================================
# AI EDGE ART GENERATOR V3.4
# app.py
# ============================================================
#
# Dynamic color palette edition.
#
# ============================================================

import io
import random

import streamlit as st

from ai_edge_generator import (
    DEFAULT_SHAPE_WEIGHTS,
)

from ai_edge_custom import (
    DEFAULT_BACKGROUND,
    DEFAULT_PALETTE,
    MIN_COLORS,
    MAX_COLORS,
    create_custom_ai_edge_blueprint,
    normalize_hex,
    render_custom_png,
    render_custom_vector,
    valid_hex,
)


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="AI Edge Art Generator",
    page_icon="◼",
    layout="centered",
)


st.title(
    "AI Edge Art Generator"
)


st.write(
    "Create an AI Edge pattern from a stable baseline, "
    "then art-direct its density, palette, color balance, "
    "and shape dominance."
)


# ============================================================
# SESSION STATE
# ============================================================

if "baseline_seed" not in st.session_state:

    st.session_state[
        "baseline_seed"
    ] = (
        random.SystemRandom()
        .randint(
            0,
            999_999_999,
        )
    )


if "generated_result" not in st.session_state:

    st.session_state[
        "generated_result"
    ] = None


if "color_count" not in st.session_state:

    st.session_state[
        "color_count"
    ] = len(
        DEFAULT_PALETTE
    )


# ============================================================
# INITIALIZE DEFAULT COLOR WIDGETS
# ============================================================

for index, slot in enumerate(
    DEFAULT_PALETTE,
    start=1,
):

    hex_key = (
        f"color_hex_{index}"
    )

    weight_key = (
        f"color_weight_{index}"
    )


    if hex_key not in st.session_state:

        st.session_state[
            hex_key
        ] = slot[
            "hex"
        ]


    if weight_key not in st.session_state:

        st.session_state[
            weight_key
        ] = slot[
            "weight"
        ]


# ============================================================
# BASELINE
# ============================================================

st.subheader(
    "Pattern Baseline"
)


st.caption(
    "Keep the same seed to preserve the same overall footprint "
    "while changing negative space, color, or shape balance."
)


seed_col, seed_button_col = st.columns(
    [
        3,
        1,
    ]
)


with seed_col:

    baseline_seed = st.number_input(
        "Baseline seed",
        min_value=0,
        max_value=999_999_999,
        value=int(
            st.session_state[
                "baseline_seed"
            ]
        ),
        step=1,
    )


with seed_button_col:

    st.write("")
    st.write("")


    if st.button(
        "New Seed",
        use_container_width=True,
    ):

        st.session_state[
            "baseline_seed"
        ] = (
            random.SystemRandom()
            .randint(
                0,
                999_999_999,
            )
        )

        st.session_state[
            "generated_result"
        ] = None

        st.rerun()


st.session_state[
    "baseline_seed"
] = int(
    baseline_seed
)


# ============================================================
# DIMENSIONS
# ============================================================

st.subheader(
    "Dimensions"
)


st.caption(
    "Patterns are constructed on a 25 × 25 px grid. "
    "Artwork may bleed beyond the requested dimensions "
    "and is cropped to the final canvas."
)


dimension_col_1, dimension_col_2 = (
    st.columns(
        2
    )
)


with dimension_col_1:

    width = st.number_input(
        "Width (px)",
        min_value=100,
        max_value=10000,
        value=1200,
        step=1,
    )


with dimension_col_2:

    height = st.number_input(
        "Height (px)",
        min_value=100,
        max_value=10000,
        value=1600,
        step=1,
    )


# ============================================================
# NEGATIVE SPACE
# ============================================================

st.subheader(
    "Negative Space"
)


negative_space = st.slider(
    "Pattern openness",
    min_value=0,
    max_value=60,
    value=15,
    step=1,
    help=(
        "15% is the default dense composition. "
        "Higher values progressively create more open areas "
        "while preserving the baseline footprint."
    ),
)


# ============================================================
# COLOR BALANCE
# ============================================================

st.subheader(
    "Color Balance"
)


st.caption(
    "Edit a hex value to change that color. "
    "Use its slider to control how dominant it is. "
    "Add additional colors whenever the palette needs more range."
)


# ============================================================
# ADD / REMOVE COLOR BUTTONS
# ============================================================

add_col, remove_col, count_col = st.columns(
    [
        1.4,
        1.4,
        2,
    ],
    vertical_alignment="center",
)


with add_col:

    add_disabled = (
        st.session_state[
            "color_count"
        ]
        >=
        MAX_COLORS
    )


    if st.button(
        "+ Add Color",
        disabled=add_disabled,
        use_container_width=True,
    ):

        new_index = (
            st.session_state[
                "color_count"
            ]
            +
            1
        )


        st.session_state[
            "color_count"
        ] = new_index


        # New colors begin inactive.
        #
        # This means adding a slot does not change the art
        # until the AD intentionally edits / activates it.

        st.session_state[
            f"color_hex_{new_index}"
        ] = "#FFFFFF"


        st.session_state[
            f"color_weight_{new_index}"
        ] = 0


        st.rerun()


with remove_col:

    remove_disabled = (
        st.session_state[
            "color_count"
        ]
        <=
        MIN_COLORS
    )


    if st.button(
        "− Remove Color",
        disabled=remove_disabled,
        use_container_width=True,
    ):

        old_index = (
            st.session_state[
                "color_count"
            ]
        )


        st.session_state.pop(
            f"color_hex_{old_index}",
            None,
        )


        st.session_state.pop(
            f"color_weight_{old_index}",
            None,
        )


        st.session_state[
            "color_count"
        ] -= 1


        st.rerun()


with count_col:

    st.caption(
        f"{st.session_state['color_count']} color slots"
    )


# ============================================================
# COLUMN HEADERS
# ============================================================

header_number, header_hex, header_swatch, header_slider = (
    st.columns(
        [
            0.4,
            1.7,
            0.7,
            4.5,
        ]
    )
)


with header_hex:

    st.caption(
        "HEX"
    )


with header_swatch:

    st.caption(
        "COLOR"
    )


with header_slider:

    st.caption(
        "BALANCE"
    )


# ============================================================
# COLOR ROWS
# ============================================================

palette_slots = []

invalid_colors = []


for index in range(
    1,
    st.session_state[
        "color_count"
    ]
    +
    1
):

    # Make sure dynamically created slots exist.

    hex_key = (
        f"color_hex_{index}"
    )

    weight_key = (
        f"color_weight_{index}"
    )


    if hex_key not in st.session_state:

        st.session_state[
            hex_key
        ] = "#FFFFFF"


    if weight_key not in st.session_state:

        st.session_state[
            weight_key
        ] = 0


    (
        number_col,
        hex_col,
        swatch_col,
        slider_col,
    ) = st.columns(
        [
            0.4,
            1.7,
            0.7,
            4.5,
        ],
        vertical_alignment="center",
    )


    # --------------------------------------------------------
    # NUMBER
    # --------------------------------------------------------

    with number_col:

        st.markdown(
            f"**{index}**"
        )


    # --------------------------------------------------------
    # HEX
    # --------------------------------------------------------

    with hex_col:

        entered_hex = st.text_input(
            f"Color {index} hex",
            key=hex_key,
            label_visibility="collapsed",
        )


    normalized = normalize_hex(
        entered_hex
    )


    # --------------------------------------------------------
    # SWATCH
    # --------------------------------------------------------

    is_valid = valid_hex(
        normalized
    )


    with swatch_col:

        preview_color = (
            normalized
            if is_valid
            else "#FFFFFF"
        )


        preview_border = (
            "rgba(0,0,0,.16)"
            if is_valid
            else "#FF0015"
        )


        st.markdown(
            (
                '<div style="'
                'width:42px;'
                'height:42px;'
                'border-radius:3px;'
                f'border:2px solid {preview_border};'
                f'background:{preview_color};'
                'margin:auto;'
                '"></div>'
            ),
            unsafe_allow_html=True,
        )


    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    with slider_col:

        weight = st.slider(
            f"Color {index} balance",
            min_value=0,
            max_value=40,
            step=1,
            key=weight_key,
            label_visibility="collapsed",
        )


    palette_slots.append(
        {
            "hex":
                normalized,

            "weight":
                weight,
        }
    )


    if not is_valid:

        invalid_colors.append(
            index
        )


# ============================================================
# BACKGROUND
# ============================================================

st.write("")

st.markdown(
    "**Background**"
)


(
    background_number,
    background_hex_col,
    background_swatch_col,
    background_empty_col,
) = st.columns(
    [
        0.4,
        1.7,
        0.7,
        4.5,
    ],
    vertical_alignment="center",
)


with background_number:

    st.markdown(
        "**B**"
    )


with background_hex_col:

    background = st.text_input(
        "Background hex",
        value=DEFAULT_BACKGROUND,
        key="background_hex",
        label_visibility="collapsed",
    )


background = normalize_hex(
    background
)


background_valid = valid_hex(
    background
)


with background_swatch_col:

    background_preview = (
        background
        if background_valid
        else "#FFFFFF"
    )


    background_border = (
        "rgba(0,0,0,.16)"
        if background_valid
        else "#FF0015"
    )


    st.markdown(
        (
            '<div style="'
            'width:42px;'
            'height:42px;'
            'border-radius:3px;'
            f'border:2px solid {background_border};'
            f'background:{background_preview};'
            'margin:auto;'
            '"></div>'
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# SHAPE DOMINANCE
# ============================================================

st.subheader(
    "Shape Dominance"
)


st.caption(
    "Increase a motif to make it more prominent. "
    "No motif disappears completely."
)


shape_weights = {}


shape_col_1, shape_col_2 = st.columns(
    2
)


with shape_col_1:

    shape_weights[
        "Checkerboard"
    ] = st.slider(
        "Checkerboard",
        1,
        10,
        int(
            DEFAULT_SHAPE_WEIGHTS[
                "Checkerboard"
            ]
        ),
    )


    shape_weights[
        "Stair Step"
    ] = st.slider(
        "Stair Step",
        1,
        10,
        int(
            DEFAULT_SHAPE_WEIGHTS[
                "Stair Step"
            ]
        ),
    )


with shape_col_2:

    shape_weights[
        "Lattice"
    ] = st.slider(
        "Lattice",
        1,
        10,
        int(
            DEFAULT_SHAPE_WEIGHTS[
                "Lattice"
            ]
        ),
    )


    shape_weights[
        "Pills"
    ] = st.slider(
        "Pills",
        1,
        10,
        int(
            DEFAULT_SHAPE_WEIGHTS[
                "Pills"
            ]
        ),
    )


# ============================================================
# SPLICE
# ============================================================

st.subheader(
    "Splice"
)


splice_enabled = st.checkbox(
    "Enable diagonal splice",
    value=True,
)


# ============================================================
# GENERATE
# ============================================================

st.write("")


if st.button(
    "Generate Pattern",
    type="primary",
    use_container_width=True,
):

    if invalid_colors:

        invalid_text = ", ".join(
            str(
                index
            )
            for index
            in invalid_colors
        )


        st.error(
            "Please enter a valid 6-digit hex value "
            f"for color slot(s): {invalid_text}."
        )


    elif not background_valid:

        st.error(
            "Please enter a valid 6-digit hex value "
            "for the background."
        )


    elif sum(
        slot[
            "weight"
        ]
        for slot
        in palette_slots
    ) <= 0:

        st.error(
            "At least one color must have "
            "a balance above zero."
        )


    else:

        with st.spinner(
            "Generating AI Edge pattern..."
        ):

            try:

                # ====================================================
                # ONE BLUEPRINT
                # ====================================================

                blueprint = (
                    create_custom_ai_edge_blueprint(
                        width=int(
                            width
                        ),

                        height=int(
                            height
                        ),

                        seed=int(
                            st.session_state[
                                "baseline_seed"
                            ]
                        ),

                        negative_space=(
                            negative_space
                        ),

                        palette_slots=(
                            palette_slots
                        ),

                        background=(
                            background
                        ),

                        shape_weights=(
                            shape_weights
                        ),

                        splice_enabled=(
                            splice_enabled
                        ),
                    )
                )


                # ====================================================
                # SAME BLUEPRINT -> PNG + VECTOR
                # ====================================================

                image = render_custom_png(
                    blueprint
                )


                production_vector = (
                    render_custom_vector(
                        blueprint
                    )
                )


                st.session_state[
                    "generated_result"
                ] = {
                    "image":
                        image,

                    "production_vector":
                        production_vector,

                    "metadata": {
                        "seed":
                            blueprint.seed,

                        "width":
                            blueprint.width,

                        "height":
                            blueprint.height,
                    },
                }


            except Exception as error:

                st.exception(
                    error
                )


# ============================================================
# RESULT
# ============================================================

result = st.session_state.get(
    "generated_result"
)


if result is not None:

    image = result[
        "image"
    ]

    production_vector = result[
        "production_vector"
    ]

    metadata = result[
        "metadata"
    ]


    st.divider()


    # ========================================================
    # PREVIEW
    # ========================================================

    st.image(
        image,
        caption=(
            "AI Edge — "
            f"Baseline {metadata['seed']}"
        ),
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


    filename_base = (
        f"ai_edge_"
        f"{metadata['seed']}_"
        f"{metadata['width']}x"
        f"{metadata['height']}"
    )


    # ========================================================
    # DOWNLOADS
    # ========================================================

    download_col_1, download_col_2 = (
        st.columns(
            2
        )
    )


    with download_col_1:

        st.download_button(
            label="Download PNG",

            data=png_buffer.getvalue(),

            file_name=(
                filename_base
                +
                ".png"
            ),

            mime="image/png",

            use_container_width=True,
        )


    with download_col_2:

        st.download_button(
            label="Download Production Vector",

            data=production_vector,

            file_name=(
                filename_base
                +
                "_production.svg"
            ),

            mime="image/svg+xml",

            use_container_width=True,
        )


    st.info(
        "Baseline seed: "
        f"{metadata['seed']}. "
        "Keep this seed to preserve the same footprint while "
        "changing negative space, palette, color balance, "
        "and shape dominance."
    )