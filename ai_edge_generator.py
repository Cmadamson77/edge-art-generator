import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw


# ============================================================
# AI EDGE PATTERN GENERATOR v2
# ============================================================
#
# COMPLETE STANDALONE SCRIPT
#
# AI Edge v2 keeps the successful v1 pattern language:
#
# - cream paper
# - dense textile / quilt construction
# - AI-specific factory / ladder / stepped motifs
# - checker, circles, diamonds and capsule support motifs
# - grid-locked geometry
# - supersampled crisp rendering
# - diagonal splice
# - shimmer
#
# V2 CHANGE:
#
# TRUE gradients now live INSIDE shapes and clusters.
#
# A gradient region creates one continuous gradient field.
# Every shape inside that region reveals a portion of that
# same field.
#
# This creates:
#
# - gradients inside large blocks
# - gradients across capsule groups
# - gradients across repeated circles
# - continuous color transitions through pattern clusters
#
# instead of:
#
# - one flat color per shape
# - "shimmer pretending to be a gradient"
#
# Dependencies:
#
#     pip install pillow numpy
#
# Run:
#
#     python3 ai_edge_pattern_v2.py
#
# ============================================================


# ============================================================
# 1. GLOBAL SETTINGS
# ============================================================

SUPERSAMPLE = 4

PAPER = "#EAE7D9"

OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1600

# None = different artwork every run.
# Set an integer to recreate the same artwork.
SEED = None


# ------------------------------------------------------------
# COLOR / EFFECT FREQUENCY
# ------------------------------------------------------------

# Requested approximately 30–40%.
TRUE_GRADIENT_REGION_PROBABILITY = 0.0

# Shimmer remains separate from gradients.
SHIMMER_REGION_PROBABILITY = 0.0

# Strong Edge splice presence.
SPLICE_REGION_PROBABILITY = 0.66


# ------------------------------------------------------------
# MOTIF WEIGHTING
# ------------------------------------------------------------

# Keeps AI-specific vocabulary dominant,
# while retaining textile variety.
AI_MOTIF_WEIGHT = 0.70


# ------------------------------------------------------------
# TEXTURE
# ------------------------------------------------------------

PRINT_GRAIN = 0.55


# ============================================================
# 2. AI EDGE COLOR SYSTEM
# ============================================================

PALETTE = {
    "blue": ["#416CA4"],
    "brown": ["#4B190F"],
    "pink": ["#F9BFF9"],
    "yellow": ["#FFFF8F"],
    "red": ["#FF0015"],
    "slate": ["#A6B5C2"],
}


# ============================================================
# 3. CURATED AI EDGE TRUE GRADIENTS
# ============================================================
#
# These are treated as LARGE events.
#
# A gradient should span an entire motif region,
# not restart inside every shape.
#
# ============================================================

AI_GRADIENTS = [

    # cream-orange -> signal red
    (
        "#FFD4A7",
        "#FF0015",
    ),

    # pale lavender -> burgundy
    (
        "#EBC2F5",
        "#740912",
    ),

    # heritage brown -> electric purple
    (
        "#753C0F",
        "#A92CFF",
    ),

    # pale blue -> electric blue
    (
        "#CFD4D3",
        "#449491",
    ),
]


# ============================================================
# 4. RANDOM INITIALIZATION
# ============================================================

if SEED is None:

    SEED = random.randint(
        0,
        999_999_999,
    )

random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# 5. BASIC COLOR HELPERS
# ============================================================

def hex_to_rgb(value):

    value = value.lstrip("#")

    return tuple(
        int(
            value[i:i + 2],
            16,
        )
        for i in (
            0,
            2,
            4,
        )
    )


def clamp(
    value,
    minimum,
    maximum,
):

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def mix_rgb(
    color_a,
    color_b,
    t,
):

    t = clamp(
        t,
        0.0,
        1.0,
    )

    return tuple(
        int(
            color_a[i]
            *
            (
                1.0 - t
            )
            +
            color_b[i]
            *
            t
        )
        for i in range(3)
    )


def adjust_rgb(
    color,
    amount,
):

    result = []

    for channel in color:

        if amount >= 0:

            value = (
                channel
                +
                (
                    255 - channel
                )
                *
                amount
            )

        else:

            value = (
                channel
                *
                (
                    1 + amount
                )
            )

        result.append(
            int(
                clamp(
                    value,
                    0,
                    255,
                )
            )
        )

    return tuple(result)


def rgba(
    color,
    alpha=255,
):

    return (
        color[0],
        color[1],
        color[2],
        alpha,
    )


def family_rgb(
    family,
):

    return [
        hex_to_rgb(value)
        for value in PALETTE[family]
    ]


def palette_color(
    family,
    index,
):

    colors = family_rgb(family)

    index = int(
        clamp(
            index,
            0,
            len(colors) - 1,
        )
    )

    return colors[index]


# ============================================================
# 6. CONTINUOUS PALETTE SAMPLING
# ============================================================

def sample_family(
    family,
    t,
):

    colors = family_rgb(family)

    t = clamp(
        t,
        0,
        1,
    )

    position = (
        t
        *
        (
            len(colors) - 1
        )
    )

    left = int(
        math.floor(position)
    )

    right = min(
        len(colors) - 1,
        left + 1,
    )

    local_t = (
        position
        -
        left
    )

    return mix_rgb(
        colors[left],
        colors[right],
        local_t,
    )


def sample_gradient(
    pair,
    t,
):

    return mix_rgb(
        hex_to_rgb(
            pair[0]
        ),
        hex_to_rgb(
            pair[1]
        ),
        t,
    )


# ============================================================
# 7. LOCKED DUAL GRID
# ============================================================

def divisors(number):

    values = []

    for i in range(
        1,
        int(
            math.sqrt(number)
        ) + 1,
    ):

        if number % i == 0:

            values.append(i)

            if i != number // i:

                values.append(
                    number // i
                )

    return sorted(values)


def choose_grid(
    width,
    height,
):

    common = math.gcd(
        width,
        height,
    )

    candidates = [
        d
        for d in divisors(common)
        if 18 <= d <= 40
    ]

    if candidates:

        preferred = random.choice(
            [
                20,
                24,
                25,
                30,
                32,
            ]
        )

        small_unit = min(
            candidates,
            key=lambda d: abs(
                d - preferred
            ),
        )

    else:

        small_unit = max(
            12,
            int(
                min(
                    width,
                    height,
                )
                /
                48
            ),
        )

    subdivision = random.choice(
        [
            4,
            5,
            6,
        ]
    )

    large_unit = (
        small_unit
        *
        subdivision
    )

    return (
        large_unit,
        small_unit,
        subdivision,
    )


# ============================================================
# 8. SUPERSAMPLING
# ============================================================

def hi(value):

    return int(
        round(
            value
            *
            SUPERSAMPLE
        )
    )


def hi_bbox(bbox):

    return tuple(
        hi(v)
        for v in bbox
    )


# ============================================================
# 9. SHAPE MASKS
# ============================================================

def shape_mask_local(
    width,
    height,
    shape,
):

    mask = Image.new(
        "L",
        (
            width,
            height,
        ),
        0,
    )

    draw = ImageDraw.Draw(
        mask
    )

    w = width
    h = height

    if shape == "circle":

        size = min(
            w,
            h,
        )

        cx = w / 2
        cy = h / 2

        draw.ellipse(
            (
                int(
                    round(
                        cx - size / 2
                    )
                ),
                int(
                    round(
                        cy - size / 2
                    )
                ),
                int(
                    round(
                        cx + size / 2
                    )
                ),
                int(
                    round(
                        cy + size / 2
                    )
                ),
            ),
            fill=255,
        )

    elif shape == "capsule":

        radius = int(
            min(
                w,
                h,
            )
            /
            2
        )

        draw.rounded_rectangle(
            (
                0,
                0,
                w,
                h,
            ),
            radius=radius,
            fill=255,
        )

    elif shape == "diamond":

        cx = int(
            round(
                w / 2
            )
        )

        cy = int(
            round(
                h / 2
            )
        )

        draw.polygon(
            [
                (
                    cx,
                    0,
                ),
                (
                    w,
                    cy,
                ),
                (
                    cx,
                    h,
                ),
                (
                    0,
                    cy,
                ),
            ],
            fill=255,
        )

    elif shape == "triangle_up":

        draw.polygon(
            [
                (
                    int(
                        w / 2
                    ),
                    0,
                ),
                (
                    w,
                    h,
                ),
                (
                    0,
                    h,
                ),
            ],
            fill=255,
        )

    elif shape == "triangle_down":

        draw.polygon(
            [
                (
                    0,
                    0,
                ),
                (
                    w,
                    0,
                ),
                (
                    int(
                        w / 2
                    ),
                    h,
                ),
            ],
            fill=255,
        )

    else:

        draw.rectangle(
            (
                0,
                0,
                w,
                h,
            ),
            fill=255,
        )

    return mask


# ============================================================
# 10. GRID-ALIGNED 45° SPLICE MASK
# ============================================================

def create_splice_mask(
    width,
    height,
    small_unit,
    direction,
    position,
):

    mask = Image.new(
        "L",
        (
            hi(width),
            hi(height),
        ),
        0,
    )

    draw = ImageDraw.Draw(
        mask
    )

    span = (
        width
        +
        height
    )

    if direction == "down":

        raw_b = (
            position
            *
            span
            -
            width
        )

        b = (
            round(
                raw_b
                /
                small_unit
            )
            *
            small_unit
        )

        polygon = [

            (
                hi(0),
                hi(b),
            ),

            (
                hi(width),
                hi(
                    width + b
                ),
            ),

            (
                hi(width),
                hi(
                    height
                    +
                    width
                    +
                    small_unit
                ),
            ),

            (
                hi(0),
                hi(
                    height
                    +
                    small_unit
                ),
            ),
        ]

    else:

        raw_b = (
            position
            *
            span
        )

        b = (
            round(
                raw_b
                /
                small_unit
            )
            *
            small_unit
        )

        polygon = [

            (
                hi(0),
                hi(
                    -height
                    -
                    small_unit
                ),
            ),

            (
                hi(width),
                hi(
                    -height
                    -
                    small_unit
                ),
            ),

            (
                hi(width),
                hi(
                    b - width
                ),
            ),

            (
                hi(0),
                hi(b),
            ),
        ]

    draw.polygon(
        polygon,
        fill=255,
    )

    return mask


# ============================================================
# 11. SHIMMER ENGINE
# ============================================================

def directional_t(
    row,
    col,
    rows,
    cols,
    axis,
):

    if axis == "x":

        return (
            col
            /
            max(
                1,
                cols - 1,
            )
        )

    if axis == "y":

        return (
            row
            /
            max(
                1,
                rows - 1,
            )
        )

    if axis == "diag_down":

        return (
            row + col
        ) / max(
            1,
            rows
            +
            cols
            -
            2,
        )

    return (
        row
        +
        (
            cols - 1 - col
        )
    ) / max(
        1,
        rows
        +
        cols
        -
        2,
    )


def shimmer_adjustment(
    t,
    phase,
):

    wave = math.sin(
        (
            t
            *
            math.pi
            *
            3.0
        )
        +
        phase
    )

    wave += (
        0.35
        *
        math.sin(
            (
                t
                *
                math.pi
                *
                6.0
            )
            -
            phase
            *
            0.7
        )
    )

    return (
        wave
        *
        0.075
    )


def region_spot_color(
    row,
    col,
    rows,
    cols,
    settings,
):

    t = directional_t(
        row,
        col,
        rows,
        cols,
        settings["gradient_axis"],
    )

    base = sample_family(
        settings["family"],
        t,
    )

    if settings["shimmer"]:

        base = adjust_rgb(
            base,
            shimmer_adjustment(
                t,
                settings["shimmer_phase"],
            ),
        )

    return base


# ============================================================
# 12. TRUE CONTINUOUS GRADIENT ENGINE
# ============================================================

def make_true_gradient_patch(
    bbox,
    region,
    settings,
):

    x0, y0, x1, y1 = bbox

    w = max(
        1,
        hi(
            x1 - x0
        ),
    )

    h = max(
        1,
        hi(
            y1 - y0
        ),
    )

    pair = settings[
        "gradient_pair"
    ]

    start = np.array(
        hex_to_rgb(
            pair[0]
        ),
        dtype=np.float32,
    )

    end = np.array(
        hex_to_rgb(
            pair[1]
        ),
        dtype=np.float32,
    )

    xs = (
        x0
        +
        np.arange(w)
        /
        SUPERSAMPLE
    )

    ys = (
        y0
        +
        np.arange(h)
        /
        SUPERSAMPLE
    )

    xx, yy = np.meshgrid(
        xs,
        ys,
    )

    rx0, ry0, rx1, ry1 = region

    rw = max(
        1.0,
        rx1 - rx0,
    )

    rh = max(
        1.0,
        ry1 - ry0,
    )

    nx = np.clip(
        (
            xx - rx0
        )
        /
        rw,
        0.0,
        1.0,
    )

    ny = np.clip(
        (
            yy - ry0
        )
        /
        rh,
        0.0,
        1.0,
    )

    axis = settings[
        "gradient_axis"
    ]

    if axis == "x":

        t = nx

    elif axis == "y":

        t = ny

    elif axis == "diag_down":

        t = (
            nx + ny
        ) / 2.0

    else:

        t = (
            nx
            +
            (
                1.0 - ny
            )
        ) / 2.0

    # Soft eased transition.
    #
    # This makes the gradients feel more printed and less
    # like a generic software preset.

    t = (
        t
        *
        t
        *
        (
            3.0
            -
            2.0
            *
            t
        )
    )

    arr = (
        start[
            None,
            None,
            :
        ]
        *
        (
            1.0
            -
            t[
                :,
                :,
                None
            ]
        )
        +
        end[
            None,
            None,
            :
        ]
        *
        t[
            :,
            :,
            None
        ]
    )

    # --------------------------------------------------------
    # SUBTLE SHIMMER ON TRUE GRADIENTS
    # --------------------------------------------------------
    #
    # Still separate — just gently modulates the printed field.
    #
    # --------------------------------------------------------

    if settings["shimmer"]:

        phase = settings[
            "shimmer_phase"
        ]

        shimmer = (
            np.sin(
                (
                    t
                    *
                    math.pi
                    *
                    2.25
                )
                +
                phase
            )
            *
            7.0
        )

        shimmer += (
            np.sin(
                (
                    t
                    *
                    math.pi
                    *
                    4.5
                )
                -
                phase
                *
                0.6
            )
            *
            2.5
        )

        arr += shimmer[
            :,
            :,
            None
        ]

    arr = np.clip(
        arr,
        0,
        255,
    ).astype(
        np.uint8
    )

    alpha = np.full(
        (
            h,
            w,
            1,
        ),
        238,
        dtype=np.uint8,
    )

    rgba_arr = np.concatenate(
        [
            arr,
            alpha,
        ],
        axis=2,
    )

    return Image.fromarray(
        rgba_arr,
        "RGBA",
    )


# ============================================================
# 13. DRAW SHAPE
# ============================================================

def draw_shape(
    canvas,
    bbox,
    shape,
    color_a,
    color_b=None,
    splice_mask=None,
    alpha=236,
    gradient_patch=None,
):

    x0, y0, x1, y1 = hi_bbox(
        bbox
    )

    cx0 = max(
        0,
        x0,
    )

    cy0 = max(
        0,
        y0,
    )

    cx1 = min(
        canvas.size[0],
        x1,
    )

    cy1 = min(
        canvas.size[1],
        y1,
    )

    if (
        cx1 <= cx0
        or
        cy1 <= cy0
    ):

        return

    full_w = max(
        1,
        x1 - x0,
    )

    full_h = max(
        1,
        y1 - y0,
    )

    mask = shape_mask_local(
        full_w,
        full_h,
        shape,
    )

    crop_box = (
        cx0 - x0,
        cy0 - y0,
        cx1 - x0,
        cy1 - y0,
    )

    mask = mask.crop(
        crop_box
    )

    patch_size = (
        cx1 - cx0,
        cy1 - cy0,
    )

    if gradient_patch is not None:

        primary_layer = gradient_patch.crop(
            crop_box
        )

    else:

        primary_layer = Image.new(
            "RGBA",
            patch_size,
            rgba(
                color_a,
                alpha,
            ),
        )

    # --------------------------------------------------------
    # NO SPLICE
    # --------------------------------------------------------

    if (
        splice_mask is None
        or
        color_b is None
    ):

        canvas.paste(
            primary_layer,
            (
                cx0,
                cy0,
            ),
            mask,
        )

        return

    # --------------------------------------------------------
    # SPLICE
    # --------------------------------------------------------

    splice_crop = splice_mask.crop(
        (
            cx0,
            cy0,
            cx1,
            cy1,
        )
    )

    side_a = ImageChops.multiply(
        mask,
        splice_crop,
    )

    side_b = ImageChops.multiply(
        mask,
        ImageChops.invert(
            splice_crop
        ),
    )

    canvas.paste(
        primary_layer,
        (
            cx0,
            cy0,
        ),
        side_a,
    )

    splice_layer = Image.new(
        "RGBA",
        patch_size,
        rgba(
            color_b,
            alpha,
        ),
    )

    canvas.paste(
        splice_layer,
        (
            cx0,
            cy0,
        ),
        side_b,
    )


# ============================================================
# 14. GRID HELPERS
# ============================================================

def region_grid(
    region,
    small_unit,
):

    x0, y0, x1, y1 = region

    cols = max(
        1,
        int(
            (
                x1 - x0
            )
            //
            small_unit
        ),
    )

    rows = max(
        1,
        int(
            (
                y1 - y0
            )
            //
            small_unit
        ),
    )

    return (
        cols,
        rows,
    )


def cell_box(
    region,
    row,
    col,
    small_unit,
    span_c=1,
    span_r=1,
):

    x0, y0, _, _ = region

    return (

        x0
        +
        col
        *
        small_unit,

        y0
        +
        row
        *
        small_unit,

        x0
        +
        (
            col + span_c
        )
        *
        small_unit,

        y0
        +
        (
            row + span_r
        )
        *
        small_unit,
    )


# ============================================================
# 15. SPLICE COLOR
# ============================================================

def choose_splice_color(
    base_family,
):

    options = [
        family
        for family in PALETTE
        if family != base_family
    ]

    splice_family = random.choice(
        options
    )

    splice_index = random.choice(
        [
            0,
            1,
            1,
            2,
        ]
    )

    return palette_color(
        splice_family,
        splice_index,
    )


# ============================================================
# 16. SINGLE SHAPE RENDERER
# ============================================================

def render_shape(
    canvas,
    bbox,
    shape,
    row,
    col,
    rows,
    cols,
    settings,
    splice_mask,
    region,
):

    if settings["gradient"]:

        gradient_patch = make_true_gradient_patch(
            bbox,
            region,
            settings,
        )

        color_a = sample_gradient(
            settings[
                "gradient_pair"
            ],
            0.5,
        )

    else:

        gradient_patch = None

        color_a = region_spot_color(
            row,
            col,
            rows,
            cols,
            settings,
        )

    splice_color = None
    active_mask = None

    if settings["splice"]:

        splice_color = settings[
            "splice_color"
        ]

        active_mask = splice_mask

    draw_shape(
        canvas,
        bbox,
        shape,
        color_a,
        splice_color,
        active_mask,
        random.randint(
            224,
            244,
        ),
        gradient_patch=gradient_patch,
    )


# ============================================================
# 17. AI MOTIF — FACTORY / SAWTOOTH
# ============================================================

def motif_factory(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    if rows < 3:

        return

    roof_row = random.randint(
        0,
        max(
            0,
            rows // 3,
        ),
    )

    for col in range(
        0,
        cols,
        2,
    ):

        if col + 1 >= cols:

            break

        render_shape(
            canvas,
            cell_box(
                region,
                roof_row,
                col,
                small_unit,
            ),
            "triangle_up",
            roof_row,
            col,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )

        render_shape(
            canvas,
            cell_box(
                region,
                roof_row,
                col + 1,
                small_unit,
            ),
            "rect",
            roof_row,
            col + 1,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )

    for row in range(
        roof_row + 1,
        rows,
    ):

        for col in range(cols):

            render_shape(
                canvas,
                cell_box(
                    region,
                    row,
                    col,
                    small_unit,
                ),
                "rect",
                row,
                col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )


# ============================================================
# 18. AI MOTIF — LADDER
# ============================================================

def motif_ladder(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    if cols < 3:

        return

    spine = cols // 2

    for row in range(rows):

        render_shape(
            canvas,
            cell_box(
                region,
                row,
                spine,
                small_unit,
            ),
            "rect",
            row,
            spine,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )

    for row in range(
        0,
        rows,
        2,
    ):

        arm = random.choice(
            [
                1,
                2,
                2,
                3,
            ]
        )

        left = max(
            0,
            spine - arm,
        )

        right = min(
            cols,
            spine + arm + 1,
        )

        for col in range(
            left,
            right,
        ):

            if col == spine:

                continue

            render_shape(
                canvas,
                cell_box(
                    region,
                    row,
                    col,
                    small_unit,
                ),
                "rect",
                row,
                col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )


# ============================================================
# 19. AI MOTIF — STAGGERED BLOCKS
# ============================================================

def motif_staggered_blocks(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    row = 0

    while row < rows:

        offset = (
            row % 4
        ) // 2

        col = offset

        while col < cols:

            span_c = random.choice(
                [
                    2,
                    3,
                    3,
                    4,
                ]
            )

            span_r = random.choice(
                [
                    1,
                    1,
                    2,
                ]
            )

            span_c = min(
                span_c,
                cols - col,
            )

            span_r = min(
                span_r,
                rows - row,
            )

            render_shape(
                canvas,
                cell_box(
                    region,
                    row,
                    col,
                    small_unit,
                    span_c=span_c,
                    span_r=span_r,
                ),
                "rect",
                row,
                col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )

            col += (
                span_c
                +
                random.choice(
                    [
                        0,
                        1,
                    ]
                )
            )

        row += random.choice(
            [
                1,
                2,
            ]
        )


# ============================================================
# 20. SUPPORT MOTIF — CIRCLES
# ============================================================

def motif_circles(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    for row in range(rows):

        for col in range(cols):

            render_shape(
                canvas,
                cell_box(
                    region,
                    row,
                    col,
                    small_unit,
                ),
                "circle",
                row,
                col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )


# ============================================================
# 21. SUPPORT MOTIF — DIAMONDS
# ============================================================

def motif_diamonds(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    for row in range(rows):

        for col in range(cols):

            render_shape(
                canvas,
                cell_box(
                    region,
                    row,
                    col,
                    small_unit,
                ),
                "diamond",
                row,
                col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )


# ============================================================
# 22. SUPPORT MOTIF — CAPSULE WEAVE
# ============================================================

def motif_capsules(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    horizontal = (
        random.random()
        <
        0.5
    )

    if horizontal:

        for row in range(rows):

            col = 0

            while col < cols:

                span = min(
                    random.choice(
                        [
                            2,
                            2,
                            3,
                            4,
                        ]
                    ),
                    cols - col,
                )

                render_shape(
                    canvas,
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                        span_c=span,
                    ),
                    "capsule",
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                    splice_mask,
                    region,
                )

                col += (
                    span
                    +
                    random.choice(
                        [
                            0,
                            0,
                            1,
                        ]
                    )
                )

    else:

        for col in range(cols):

            row = 0

            while row < rows:

                span = min(
                    random.choice(
                        [
                            2,
                            2,
                            3,
                            4,
                        ]
                    ),
                    rows - row,
                )

                render_shape(
                    canvas,
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                        span_r=span,
                    ),
                    "capsule",
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                    splice_mask,
                    region,
                )

                row += (
                    span
                    +
                    random.choice(
                        [
                            0,
                            0,
                            1,
                        ]
                    )
                )


# ============================================================
# 23. SUPPORT MOTIF — CHECKER
# ============================================================

def motif_checker(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    for row in range(rows):

        for col in range(cols):

            if (
                row + col
            ) % 2 == 0:

                render_shape(
                    canvas,
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                    ),
                    "rect",
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                    splice_mask,
                    region,
                )


# ============================================================
# 24. SUPPORT MOTIF — WOVEN BARS
# ============================================================

def motif_woven(
    canvas,
    region,
    small_unit,
    settings,
    splice_mask,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    for row in range(rows):

        if row % 2 == 0:

            col = 0

            while col < cols:

                span = min(
                    2,
                    cols - col,
                )

                render_shape(
                    canvas,
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                        span_c=span,
                    ),
                    "rect",
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                    splice_mask,
                    region,
                )

                col += 3

        else:

            for col in range(
                1,
                cols,
                3,
            ):

                render_shape(
                    canvas,
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                    ),
                    "rect",
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                    splice_mask,
                    region,
                )


# ============================================================
# 25. MOTIF TABLE
# ============================================================

AI_MOTIFS = [

    "factory",
    "factory",
    "factory",

    "ladder",
    "ladder",

    "staggered",
    "staggered",
]


SUPPORT_MOTIFS = [

    "circles",
    "diamonds",
    "capsules",
    "checker",
    "woven",
]


def choose_motif():

    if (
        random.random()
        <
        AI_MOTIF_WEIGHT
    ):

        return random.choice(
            AI_MOTIFS
        )

    return random.choice(
        SUPPORT_MOTIFS
    )


# ============================================================
# 26. MOTIF DISPATCH
# ============================================================

def render_motif(
    canvas,
    region,
    motif,
    small_unit,
    settings,
    splice_mask,
):

    if motif == "factory":

        motif_factory(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "ladder":

        motif_ladder(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "staggered":

        motif_staggered_blocks(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "circles":

        motif_circles(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "diamonds":

        motif_diamonds(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "capsules":

        motif_capsules(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "checker":

        motif_checker(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    else:

        motif_woven(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )


# ============================================================
# 27. MACRO REGION CONSTRUCTION
# ============================================================

def build_macro_regions(
    width,
    height,
    large_unit,
):

    cols = int(
        math.ceil(
            width
            /
            large_unit
        )
    )

    rows = int(
        math.ceil(
            height
            /
            large_unit
        )
    )

    regions = []

    occupied = np.zeros(
        (
            rows,
            cols,
        ),
        dtype=bool,
    )

    attempts = 0

    while (
        not occupied.all()
        and
        attempts < 800
    ):

        attempts += 1

        empty = np.argwhere(
            occupied == False
        )

        if len(empty) == 0:

            break

        choice_index = random.randrange(
            len(empty)
        )

        start_r, start_c = empty[
            choice_index
        ]

        span_c = random.choice(
            [
                1,
                1,
                1,
                2,
                2,
                2,
                3,
            ]
        )

        span_r = random.choice(
            [
                1,
                1,
                1,
                2,
                2,
                2,
                3,
            ]
        )

        end_c = min(
            cols,
            start_c + span_c,
        )

        end_r = min(
            rows,
            start_r + span_r,
        )

        if occupied[
            start_r:end_r,
            start_c:end_c
        ].any():

            continue

        occupied[
            start_r:end_r,
            start_c:end_c
        ] = True

        x0 = (
            start_c
            *
            large_unit
        )

        y0 = (
            start_r
            *
            large_unit
        )

        x1 = min(
            width,
            end_c
            *
            large_unit,
        )

        y1 = min(
            height,
            end_r
            *
            large_unit,
        )

        regions.append(
            (
                x0,
                y0,
                x1,
                y1,
            )
        )

    return regions


# ============================================================
# 28. CREAM PAPER
# ============================================================

def make_paper(
    width,
    height,
):

    base = np.array(
        hex_to_rgb(
            PAPER
        ),
        dtype=np.float32,
    )

    h = hi(height)
    w = hi(width)

    arr = np.empty(
        (
            h,
            w,
            3,
        ),
        dtype=np.float32,
    )

    arr[:, :] = base

    grain = np.random.normal(
        0,
        0.24,
        (
            h,
            w,
            1,
        ),
    )

    arr += grain

    return Image.fromarray(
        np.clip(
            arr,
            0,
            255,
        ).astype(
            np.uint8
        )
    )


# ============================================================
# 29. REGION SETTINGS
# ============================================================

def create_region_settings():

    family = random.choice(
        list(
            PALETTE.keys()
        )
    )

    gradient = (
        random.random()
        <
        TRUE_GRADIENT_REGION_PROBABILITY
    )

    shimmer = (
        random.random()
        <
        SHIMMER_REGION_PROBABILITY
    )

    splice = (
        random.random()
        <
        SPLICE_REGION_PROBABILITY
    )

    return {

        "family":
            family,

        "gradient":
            gradient,

        "gradient_pair":
            random.choice(
                AI_GRADIENTS
            ),

        # Horizontal / vertical gradients dominate.
        #
        # Diagonal remains rarer because the splice already
        # creates strong diagonal movement.

        "gradient_axis":
            random.choice(
                [
                    "x",
                    "x",
                    "x",
                    "y",
                    "y",
                    "diag_down",
                ]
            ),

        "shimmer":
            shimmer,

        "shimmer_phase":
            random.uniform(
                0,
                math.pi * 2,
            ),

        "splice":
            splice,

        "splice_color":
            choose_splice_color(
                family
            ),
    }


# ============================================================
# 30. QUIET GRID OVERPRINT
# ============================================================

def add_overprint(
    canvas,
    width,
    height,
    small_unit,
):

    if random.random() > 0.42:

        return

    family = random.choice(
        list(
            PALETTE.keys()
        )
    )

    color = palette_color(
        family,
        0,
    )

    overlay = Image.new(
        "RGBA",
        canvas.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    direction = random.choice(
        [
            "horizontal",
            "vertical",
        ]
    )

    stripe_count = random.randint(
        2,
        4,
    )

    if direction == "horizontal":

        max_rows = max(
            1,
            height
            //
            small_unit,
        )

        start = random.randint(
            0,
            max_rows - 1,
        )

        for i in range(
            stripe_count
        ):

            row = (
                start
                +
                i * 2
            ) % max_rows

            y0 = hi(
                row
                *
                small_unit
            )

            y1 = hi(
                (
                    row + 1
                )
                *
                small_unit
            )

            draw.rectangle(
                (
                    0,
                    y0,
                    hi(width),
                    y1,
                ),
                fill=rgba(
                    color,
                    random.randint(
                        10,
                        24,
                    ),
                ),
            )

    else:

        max_cols = max(
            1,
            width
            //
            small_unit,
        )

        start = random.randint(
            0,
            max_cols - 1,
        )

        for i in range(
            stripe_count
        ):

            col = (
                start
                +
                i * 2
            ) % max_cols

            x0 = hi(
                col
                *
                small_unit
            )

            x1 = hi(
                (
                    col + 1
                )
                *
                small_unit
            )

            draw.rectangle(
                (
                    x0,
                    0,
                    x1,
                    hi(height),
                ),
                fill=rgba(
                    color,
                    random.randint(
                        10,
                        24,
                    ),
                ),
            )

    canvas.alpha_composite(
        overlay
    )


# ============================================================
# 31. FINAL PRINT GRAIN
# ============================================================

def apply_print_texture(
    image,
):

    arr = np.array(
        image
    ).astype(
        np.float32
    )

    height, width = arr.shape[:2]

    fine_noise = np.random.normal(
        0,
        PRINT_GRAIN,
        (
            height,
            width,
            1,
        ),
    )

    arr += fine_noise

    return Image.fromarray(
        np.clip(
            arr,
            0,
            255,
        ).astype(
            np.uint8
        )
    )


# ============================================================
# 32. MAIN GENERATOR
# ============================================================

def generate_ai_edge_pattern(
    width,
    height,
):

    paper = make_paper(
        width,
        height,
    )

    canvas = paper.convert(
        "RGBA"
    )

    (
        large_unit,
        small_unit,
        subdivision,
    ) = choose_grid(
        width,
        height,
    )

    # --------------------------------------------------------
    # GLOBAL GRID-ALIGNED SPLICE
    # --------------------------------------------------------

    splice_direction = random.choice(
        [
            "down",
            "up",
        ]
    )

    splice_position = random.uniform(
        0.24,
        0.69,
    )

    splice_mask = create_splice_mask(
        width,
        height,
        small_unit,
        splice_direction,
        splice_position,
    )

    # --------------------------------------------------------
    # MACRO PATCHWORK
    # --------------------------------------------------------

    regions = build_macro_regions(
        width,
        height,
        large_unit,
    )

    previous_motif = None
    previous_settings = None

    gradient_regions = 0
    shimmer_regions = 0
    splice_regions = 0

    for region in regions:

        # ----------------------------------------------------
        # REPEAT MOTIFS FREQUENTLY
        # ----------------------------------------------------
        #
        # This is one of the most important parts of the
        # successful textile feeling.
        #
        # ----------------------------------------------------

        if (
            previous_motif is not None
            and
            random.random() < 0.50
        ):

            motif = previous_motif

        else:

            motif = choose_motif()

        # ----------------------------------------------------
        # OCCASIONALLY REPEAT COLOR LANGUAGE TOO
        # ----------------------------------------------------

        if (
            previous_settings is not None
            and
            random.random() < 0.28
        ):

            settings = dict(
                previous_settings
            )

            settings[
                "shimmer_phase"
            ] += random.uniform(
                -0.65,
                0.65,
            )

        else:

            settings = create_region_settings()

        if settings["gradient"]:

            gradient_regions += 1

        if settings["shimmer"]:

            shimmer_regions += 1

        if settings["splice"]:

            splice_regions += 1

        render_motif(
            canvas,
            region,
            motif,
            small_unit,
            settings,
            splice_mask,
        )

        previous_motif = motif
        previous_settings = settings

    # --------------------------------------------------------
    # QUIET PRINT OVERLAY
    # --------------------------------------------------------

    add_overprint(
        canvas,
        width,
        height,
        small_unit,
    )

    # --------------------------------------------------------
    # DOWNSAMPLE ONCE
    # --------------------------------------------------------

    result = canvas.convert(
        "RGB"
    ).resize(
        (
            width,
            height,
        ),
        Image.Resampling.LANCZOS,
    )

    result = apply_print_texture(
        result
    )

    metadata = {

        "seed":
            SEED,

        "small_unit":
            small_unit,

        "large_unit":
            large_unit,

        "subdivision":
            subdivision,

        "region_count":
            len(regions),

        "gradient_regions":
            gradient_regions,

        "shimmer_regions":
            shimmer_regions,

        "splice_regions":
            splice_regions,

        "splice_direction":
            splice_direction,
    }

    return (
        result,
        metadata,
    )


# ============================================================
# 33. LOCAL VS CODE RUNNER
# ============================================================

if __name__ == "__main__":

    art, info = generate_ai_edge_pattern(
        OUTPUT_WIDTH,
        OUTPUT_HEIGHT,
    )

    output_id = random.randint(
        0,
        999_999_999,
    )

    filename = (
        f"ai_edge_pattern_v2_"
        f"{output_id}.png"
    )

    art.save(
        filename
    )

    print()

    print(
        "======================================"
    )

    print(
        " AI EDGE PATTERN v2 GENERATED"
    )

    print(
        "======================================"
    )

    print(
        f" Seed:             "
        f"{info['seed']}"
    )

    print(
        f" Size:             "
        f"{OUTPUT_WIDTH} x "
        f"{OUTPUT_HEIGHT}"
    )

    print(
        f" Small grid:       "
        f"{info['small_unit']} px"
    )

    print(
        f" Large grid:       "
        f"{info['large_unit']} px"
    )

    print(
        f" Macro regions:    "
        f"{info['region_count']}"
    )

    print(
        f" True gradients:   "
        f"{info['gradient_regions']}"
    )

    print(
        f" Shimmer regions:  "
        f"{info['shimmer_regions']}"
    )

    print(
        f" Splice regions:   "
        f"{info['splice_regions']}"
    )

    print(
        f" Splice direction: "
        f"{info['splice_direction']}"
    )

    print(
        f" File:             "
        f"{filename}"
    )

    print(
        "======================================"
    )