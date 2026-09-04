# ============================================================
# AI EDGE CUSTOM PALETTE LAYER
# ai_edge_custom.py
# ============================================================
#
# Supports:
#
# - dynamic artwork palette
# - 1–20 artwork colors
# - custom background
# - exact flat hex values
#
# The approved generator and vector exporter remain unchanged.
#
# ============================================================

from contextlib import contextmanager

import ai_edge_generator as generator
import ai_edge_vector as vector


# ============================================================
# DEFAULT PALETTE
# ============================================================

DEFAULT_PALETTE = [
    {
        "hex": "#4B190F",
        "weight": 14,
    },
    {
        "hex": "#F9BFF9",
        "weight": 14,
    },
    {
        "hex": "#FF0015",
        "weight": 14,
    },
    {
        "hex": "#FFFF8F",
        "weight": 14,
    },
    {
        "hex": "#416CA4",
        "weight": 16,
    },
    {
        "hex": "#A6B5C2",
        "weight": 14,
    },
    {
        "hex": "#CBFEFF",
        "weight": 14,
    },
]

DEFAULT_BACKGROUND = "#EAE7D9"

MIN_COLORS = 1
MAX_COLORS = 20


# ============================================================
# HEX HELPERS
# ============================================================

def normalize_hex(
    value,
):

    value = str(
        value
    ).strip().upper()

    if not value.startswith(
        "#"
    ):

        value = (
            "#"
            +
            value
        )

    return value


def valid_hex(
    value,
):

    value = normalize_hex(
        value
    )

    if len(
        value
    ) != 7:

        return False

    try:

        int(
            value[1:],
            16,
        )

    except ValueError:

        return False

    return True


def validated_hex(
    value,
):

    value = normalize_hex(
        value
    )

    if not valid_hex(
        value
    ):

        raise ValueError(
            f"{value} is not a valid 6-digit hex color."
        )

    return value


# ============================================================
# CONVERT DYNAMIC PALETTE
# ============================================================

def build_color_system(
    palette_slots,
):

    colors = {}
    weights = {}


    for index, slot in enumerate(
        palette_slots,
        start=1,
    ):

        name = (
            f"Color {index}"
        )

        colors[
            name
        ] = validated_hex(
            slot["hex"]
        )

        weights[
            name
        ] = max(
            0.0,
            float(
                slot["weight"]
            ),
        )


    return (
        colors,
        weights,
    )


# ============================================================
# TEMPORARY PALETTE ENVIRONMENT
# ============================================================

@contextmanager
def custom_palette_environment(
    colors,
    background,
):

    clean_colors = {
        name: validated_hex(
            value
        )
        for name, value
        in colors.items()
    }


    clean_background = (
        validated_hex(
            background
        )
    )


    original_generator_colors = (
        generator.COLORS
    )

    original_generator_background = (
        generator.BACKGROUND
    )

    original_vector_background = (
        vector.BACKGROUND
    )


    try:

        generator.COLORS = dict(
            clean_colors
        )

        generator.BACKGROUND = (
            clean_background
        )

        vector.BACKGROUND = (
            clean_background
        )

        yield


    finally:

        generator.COLORS = (
            original_generator_colors
        )

        generator.BACKGROUND = (
            original_generator_background
        )

        vector.BACKGROUND = (
            original_vector_background
        )


# ============================================================
# CREATE BLUEPRINT
# ============================================================

def create_custom_ai_edge_blueprint(
    width,
    height,
    seed,
    negative_space,
    palette_slots,
    background,
    shape_weights,
    splice_enabled=True,
):

    (
        colors,
        color_weights,
    ) = build_color_system(
        palette_slots
    )


    if sum(
        color_weights.values()
    ) <= 0:

        raise ValueError(
            "At least one artwork color must have "
            "a balance above zero."
        )


    with custom_palette_environment(
        colors=colors,
        background=background,
    ):

        blueprint = (
            generator.create_ai_edge_blueprint(
                width=width,
                height=height,
                seed=seed,
                negative_space=negative_space,
                color_weights=color_weights,
                shape_weights=shape_weights,
                splice_enabled=splice_enabled,
            )
        )


        # Store the custom background directly in the
        # finished blueprint.

        blueprint.background = (
            validated_hex(
                background
            )
        )


        return blueprint


# ============================================================
# PNG
# ============================================================

def render_custom_png(
    blueprint,
):

    return generator.render_blueprint_png(
        blueprint
    )


# ============================================================
# VECTOR
# ============================================================

def render_custom_vector(
    blueprint,
):

    original_vector_background = (
        vector.BACKGROUND
    )


    try:

        vector.BACKGROUND = (
            blueprint.background
        )


        return (
            vector.generate_vector_from_blueprint(
                blueprint
            )
        )


    finally:

        vector.BACKGROUND = (
            original_vector_background
        )