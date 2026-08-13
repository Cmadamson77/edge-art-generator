import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw


# ============================================================
# VITAL EDGE PATTERN GENERATOR v3
# ============================================================
#
# Direction:
#
# - retain successful textile / lattice construction from V2
# - introduce larger flat architectural / stair-step masses
# - make Vital feel moodier, earthier and less neon
# - remove bright lime as a dominant palette color
# - preserve cell-locking and crisp supersampled geometry
# - use true gradients selectively across whole motifs
# - keep shimmer and splice independent from gradient
# - preserve cream ground
#
# Dependencies:
#
#     pip install pillow numpy
#
# Run:
#
#     python3 Vital_Edge_V3.py
#
# ============================================================


# ============================================================
# 1. GLOBAL SETTINGS
# ============================================================

SUPERSAMPLE = 4

PAPER = "#EAE7D9"

OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1600

# None = random every run.
# Set to an integer for reproducibility.
SEED = None


# ============================================================
# 2. COMPOSITION SETTINGS
# ============================================================

# Approximate percentage of macro regions that become
# large visual anchors instead of small pattern fields.

LARGE_BLOCK_PROBABILITY = 0.27

# Gradients remain present but not everywhere.

TRUE_GRADIENT_REGION_PROBABILITY = 0.34

# Shimmer and splice are separate from gradients.

SHIMMER_REGION_PROBABILITY = 0.52
SPLICE_REGION_PROBABILITY = 0.58

# Vital-specific motifs should dominate.

VITAL_MOTIF_WEIGHT = 0.78

# High-chroma accents should be uncommon.

HIGH_CHROMA_ACCENT_PROBABILITY = 0.065

# Printed / textile surface.

PRINT_GRAIN = 0.42


# ============================================================
# 3. VITAL EDGE PALETTE
# ============================================================
#
# Important V3 change:
#
# There is NO #B2FF00.
#
# The previous acid-lime family is replaced by a much more
# olive / chartreuse / heritage progression.
#
# ============================================================

PALETTE = {

    "blue": [
        "#100B2A",
        "#153B91",
        "#2459CC",
        "#7396DA",
        "#A7BCE8",
        "#D7E0F0",
    ],

    "green": [
        "#20231F",
        "#173A17",
        "#3F5E39",
        "#71866A",
        "#9BA48E",
        "#C5C7B7",
    ],

    "berry": [
        "#52082F",
        "#7D184C",
        "#B7317F",
        "#D75591",
        "#E98BB3",
        "#F2C9D9",
    ],

    "olive": [
        "#293817",
        "#4F682D",
        "#789445",
        "#98AF58",
        "#B8CC72",
        "#E2E9BE",
    ],

    "neutral": [
        "#20231F",
        "#41453E",
        "#687065",
        "#92998A",
        "#B7B8A8",
        "#D6D3C5",
    ],
}


# ============================================================
# 4. CURATED VITAL GRADIENTS
# ============================================================
#
# These are deliberately moodier than V2.
#
# Most begin or end in middle/dark values.
#
# ============================================================

VITAL_GRADIENTS = [

    # forest -> muted olive
    (
        "#173A17",
        "#98AF58",
    ),

    # smoky blue -> cream blue
    (
        "#153B91",
        "#D7E0F0",
    ),

    # plum -> dusty rose
    (
        "#52082F",
        "#E98BB3",
    ),

    # dark green -> stone
    (
        "#20231F",
        "#B7B8A8",
    ),

    # pale blue -> muted berry
    (
        "#A7BCE8",
        "#B7317F",
    ),

    # moss -> softened chartreuse
    (
        "#3F5E39",
        "#B8CC72",
    ),

    # dark blue -> sage
    (
        "#100B2A",
        "#9BA48E",
    ),

    # berry -> mineral blue
    (
        "#7D184C",
        "#7396DA",
    ),

    # olive -> light warm neutral
    (
        "#4F682D",
        "#D6D3C5",
    ),
]


# ============================================================
# 5. HIGH-CHROMA ACCENTS
# ============================================================
#
# These colors can appear, but only rarely.
#
# ============================================================

ACCENT_COLORS = [

    "#D75591",
    "#7396DA",
    "#98AF58",
    "#B8CC72",
    "#B7317F",
]


# ============================================================
# 6. RANDOM INITIALIZATION
# ============================================================

if SEED is None:
    SEED = random.randint(
        0,
        999_999_999,
    )

random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# 7. COLOR HELPERS
# ============================================================

def hex_to_rgb(value):

    value = value.lstrip("#")

    return tuple(
        int(value[i:i + 2], 16)
        for i in (0, 2, 4)
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
            color_a[i] * (1.0 - t)
            + color_b[i] * t
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
                + (255 - channel)
                * amount
            )

        else:

            value = (
                channel
                * (1 + amount)
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


def family_rgb(family):

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
# 8. MOOD BIAS
# ============================================================
#
# A global safeguard against colors feeling overly digital,
# candy-like or neon.
#
# ============================================================

def apply_vital_mood_bias(
    color,
    strength=1.0,
):

    r, g, b = color

    average = (
        r + g + b
    ) / 3.0

    # Pull saturation toward a shared middle.
    amount = (
        0.07
        *
        strength
    )

    r = (
        r * (1 - amount)
        + average * amount
    )

    g = (
        g * (1 - amount * 0.8)
        + average * amount * 0.8
    )

    b = (
        b * (1 - amount * 0.8)
        + average * amount * 0.8
    )

    # Slight reduction in top-end brightness.
    peak = max(r, g, b)

    ceiling = 224

    if peak > ceiling:

        scale = (
            ceiling / peak
        )

        r *= scale
        g *= scale
        b *= scale

    return (
        int(clamp(r, 0, 255)),
        int(clamp(g, 0, 255)),
        int(clamp(b, 0, 255)),
    )


# ============================================================
# 9. CONTINUOUS PALETTE SAMPLING
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
        position - left
    )

    color = mix_rgb(
        colors[left],
        colors[right],
        local_t,
    )

    return apply_vital_mood_bias(
        color,
        0.75,
    )


def sample_gradient(
    pair,
    t,
):

    color = mix_rgb(
        hex_to_rgb(pair[0]),
        hex_to_rgb(pair[1]),
        t,
    )

    return apply_vital_mood_bias(
        color,
        0.55,
    )


# ============================================================
# 10. GRID
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
                ) / 48
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
# 11. SUPERSAMPLING
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
# 12. SHAPE MASKS
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

    draw = ImageDraw.Draw(mask)

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
                int(cx - size / 2),
                int(cy - size / 2),
                int(cx + size / 2),
                int(cy + size / 2),
            ),
            fill=255,
        )

    elif shape == "capsule":

        radius = int(
            min(w, h)
            / 2
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

        cx = int(w / 2)
        cy = int(h / 2)

        draw.polygon(
            [
                (cx, 0),
                (w, cy),
                (cx, h),
                (0, cy),
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
# 13. GRID-LOCKED SPLICE
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

    draw = ImageDraw.Draw(mask)

    span = (
        width + height
    )

    if direction == "down":

        raw_b = (
            position * span
            - width
        )

        b = (
            round(
                raw_b / small_unit
            )
            * small_unit
        )

        polygon = [
            (
                hi(0),
                hi(b),
            ),
            (
                hi(width),
                hi(width + b),
            ),
            (
                hi(width),
                hi(
                    height
                    + width
                    + small_unit
                ),
            ),
            (
                hi(0),
                hi(
                    height
                    + small_unit
                ),
            ),
        ]

    else:

        raw_b = (
            position * span
        )

        b = (
            round(
                raw_b / small_unit
            )
            * small_unit
        )

        polygon = [
            (
                hi(0),
                hi(
                    -height
                    - small_unit
                ),
            ),
            (
                hi(width),
                hi(
                    -height
                    - small_unit
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
# 14. SHIMMER
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
            / max(
                1,
                cols - 1,
            )
        )

    if axis == "y":

        return (
            row
            / max(
                1,
                rows - 1,
            )
        )

    if axis == "diag_down":

        return (
            row + col
        ) / max(
            1,
            rows + cols - 2,
        )

    return (
        row
        + (
            cols - 1 - col
        )
    ) / max(
        1,
        rows + cols - 2,
    )


def shimmer_adjustment(
    t,
    phase,
):

    wave = math.sin(
        (
            t
            * math.pi
            * 2.6
        )
        + phase
    )

    wave += (
        0.30
        * math.sin(
            (
                t
                * math.pi
                * 5.2
            )
            - phase
            * 0.7
        )
    )

    return (
        wave
        *
        0.065
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

    return apply_vital_mood_bias(
        base,
        0.8,
    )


# ============================================================
# 15. TRUE GRADIENT PATCH
# ============================================================

def make_true_gradient_patch(
    bbox,
    region,
    settings,
):

    x0, y0, x1, y1 = bbox

    w = max(
        1,
        hi(x1 - x0),
    )

    h = max(
        1,
        hi(y1 - y0),
    )

    pair = settings[
        "gradient_pair"
    ]

    start = np.array(
        apply_vital_mood_bias(
            hex_to_rgb(pair[0]),
            0.5,
        ),
        dtype=np.float32,
    )

    end = np.array(
        apply_vital_mood_bias(
            hex_to_rgb(pair[1]),
            0.5,
        ),
        dtype=np.float32,
    )

    xs = (
        x0
        + np.arange(w)
        / SUPERSAMPLE
    )

    ys = (
        y0
        + np.arange(h)
        / SUPERSAMPLE
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
        ) / rw,
        0.0,
        1.0,
    )

    ny = np.clip(
        (
            yy - ry0
        ) / rh,
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
            + (1.0 - ny)
        ) / 2.0

    # Smoothstep.
    t = (
        t
        * t
        * (
            3.0
            - 2.0
            * t
        )
    )

    arr = (
        start[
            None,
            None,
            :
        ]
        * (
            1.0
            - t[
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
        * t[
            :,
            :,
            None
        ]
    )

    if settings["shimmer"]:

        phase = settings[
            "shimmer_phase"
        ]

        shimmer = (
            np.sin(
                t
                * math.pi
                * 2.0
                + phase
            )
            * 4.5
        )

        shimmer += (
            np.sin(
                t
                * math.pi
                * 4.0
                - phase
                * 0.6
            )
            * 1.8
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
        240,
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
# 16. DRAW SHAPE
# ============================================================

def draw_shape(
    canvas,
    bbox,
    shape,
    color_a,
    color_b=None,
    splice_mask=None,
    alpha=238,
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
# 17. GRID HELPERS
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
            ) // small_unit
        ),
    )

    rows = max(
        1,
        int(
            (
                y1 - y0
            ) // small_unit
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
        + col
        * small_unit,

        y0
        + row
        * small_unit,

        x0
        + (
            col + span_c
        )
        * small_unit,

        y0
        + (
            row + span_r
        )
        * small_unit,
    )


# ============================================================
# 18. COLOR SELECTION
# ============================================================

def choose_primary_family():

    return random.choices(
        [
            "green",
            "blue",
            "berry",
            "olive",
            "neutral",
        ],
        weights=[
            36,
            22,
            17,
            17,
            8,
        ],
        k=1,
    )[0]


def choose_muted_palette_index():

    # Strongly favors middle and dark values.
    return random.choices(
        [
            0,
            1,
            2,
            3,
            4,
            5,
        ],
        weights=[
            14,
            24,
            28,
            22,
            9,
            3,
        ],
        k=1,
    )[0]


def choose_splice_color(
    base_family,
):

    possible = [
        family
        for family in PALETTE
        if family != base_family
    ]

    family = random.choice(
        possible
    )

    index = random.choices(
        [
            0,
            1,
            2,
            3,
        ],
        weights=[
            24,
            38,
            28,
            10,
        ],
        k=1,
    )[0]

    color = palette_color(
        family,
        index,
    )

    return apply_vital_mood_bias(
        color,
        1.0,
    )


def choose_accent_color():

    return apply_vital_mood_bias(
        hex_to_rgb(
            random.choice(
                ACCENT_COLORS
            )
        ),
        0.75,
    )


# ============================================================
# 19. REGION SETTINGS
# ============================================================

def create_region_settings(
    previous_settings=None,
):

    family = choose_primary_family()

    # --------------------------------------------------------
    # NEIGHBOR CHROMA RULE
    # --------------------------------------------------------
    #
    # If the previous area was bright/accent-heavy, force this
    # region toward green, neutral or dark blue.
    #
    # --------------------------------------------------------

    if (
        previous_settings is not None
        and previous_settings.get(
            "high_chroma",
            False,
        )
    ):

        family = random.choices(
            [
                "green",
                "neutral",
                "blue",
            ],
            weights=[
                52,
                28,
                20,
            ],
            k=1,
        )[0]

    high_chroma = (
        random.random()
        <
        HIGH_CHROMA_ACCENT_PROBABILITY
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
                VITAL_GRADIENTS
            ),

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

        "high_chroma":
            high_chroma,
    }


# ============================================================
# 20. SINGLE SHAPE RENDERER
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

    if (
        settings["high_chroma"]
        and random.random() < 0.10
    ):

        color_a = choose_accent_color()

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
            228,
            244,
        ),
        gradient_patch=gradient_patch,
    )


# ============================================================
# 21. VITAL MOTIF — FIVE-CIRCLE CROSS
# ============================================================

def motif_cellular_cross(
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

    step = 3

    for anchor_r in range(
        0,
        rows,
        step,
    ):

        for anchor_c in range(
            0,
            cols,
            step,
        ):

            points = [
                (
                    anchor_r,
                    anchor_c + 1,
                ),
                (
                    anchor_r + 1,
                    anchor_c,
                ),
                (
                    anchor_r + 1,
                    anchor_c + 1,
                ),
                (
                    anchor_r + 1,
                    anchor_c + 2,
                ),
                (
                    anchor_r + 2,
                    anchor_c + 1,
                ),
            ]

            for row, col in points:

                if (
                    row < rows
                    and
                    col < cols
                ):

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
# 22. VITAL MOTIF — LATTICE
# ============================================================

def motif_lattice(
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
                row % 2 == 0
                or
                col % 2 == 0
            ):

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
# 23. VITAL MOTIF — VERTEBRA / SPINE
# ============================================================

def motif_vertebra(
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

    center = cols // 2

    for row in range(rows):

        render_shape(
            canvas,
            cell_box(
                region,
                row,
                center,
                small_unit,
            ),
            "rect",
            row,
            center,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )

        if row % 2 == 0:

            arm = random.choice(
                [
                    1,
                    1,
                    2,
                ]
            )

            for distance in range(
                1,
                arm + 1,
            ):

                left = (
                    center - distance
                )

                right = (
                    center + distance
                )

                if left >= 0:

                    render_shape(
                        canvas,
                        cell_box(
                            region,
                            row,
                            left,
                            small_unit,
                        ),
                        "rect",
                        row,
                        left,
                        rows,
                        cols,
                        settings,
                        splice_mask,
                        region,
                    )

                if right < cols:

                    render_shape(
                        canvas,
                        cell_box(
                            region,
                            row,
                            right,
                            small_unit,
                        ),
                        "rect",
                        row,
                        right,
                        rows,
                        cols,
                        settings,
                        splice_mask,
                        region,
                    )


# ============================================================
# 24. VITAL MOTIF — OFFSET CHAIN
# ============================================================

def motif_offset_chain(
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
    col = 0

    while (
        row < rows
        and
        col < cols
    ):

        span = min(
            random.choice(
                [
                    2,
                    3,
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
            "rect",
            row,
            col,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )

        connector_col = min(
            cols - 1,
            col + span - 1,
        )

        if row + 1 < rows:

            render_shape(
                canvas,
                cell_box(
                    region,
                    row + 1,
                    connector_col,
                    small_unit,
                ),
                "rect",
                row + 1,
                connector_col,
                rows,
                cols,
                settings,
                splice_mask,
                region,
            )

        row += 2
        col += max(
            1,
            span - 1,
        )


# ============================================================
# 25. VITAL MOTIF — CAPSULE FIELD
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
        0.55
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

                col += span

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

                row += span


# ============================================================
# 26. SUPPORT MOTIF — DIAMOND FIELD
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
# 27. SUPPORT MOTIF — CHECKER
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
# 28. LARGE BLOCK — SOLID RECTANGLE
# ============================================================
#
# These intentionally interrupt the finer textile field.
#
# ============================================================

def motif_large_block(
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

    # Large blocks should usually NOT carry gradients.
    settings = dict(
        settings
    )

    settings["gradient"] = (
        random.random()
        <
        0.18
    )

    settings["shimmer"] = (
        settings["gradient"]
        and random.random() < 0.45
    )

    # Pick a large footprint.
    span_c = random.randint(
        max(
            1,
            cols // 2,
        ),
        max(
            1,
            cols,
        ),
    )

    span_r = random.randint(
        max(
            1,
            rows // 2,
        ),
        max(
            1,
            rows,
        ),
    )

    start_col = random.randint(
        0,
        max(
            0,
            cols - span_c,
        ),
    )

    start_row = random.randint(
        0,
        max(
            0,
            rows - span_r,
        ),
    )

    render_shape(
        canvas,
        cell_box(
            region,
            start_row,
            start_col,
            small_unit,
            span_c=span_c,
            span_r=span_r,
        ),
        "rect",
        start_row,
        start_col,
        rows,
        cols,
        settings,
        splice_mask,
        region,
    )


# ============================================================
# 29. LARGE BLOCK — STAIR STEP
# ============================================================

def motif_stair_block(
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

    if (
        cols < 2
        or
        rows < 2
    ):
        return

    settings = dict(
        settings
    )

    # Primarily solid.
    settings["gradient"] = (
        random.random()
        <
        0.14
    )

    direction = random.choice(
        [
            "down_right",
            "down_left",
        ]
    )

    step_width = random.choice(
        [
            1,
            2,
            2,
            3,
        ]
    )

    step_height = random.choice(
        [
            1,
            1,
            2,
        ]
    )

    if direction == "down_right":

        col = 0
        delta = step_width

    else:

        col = max(
            0,
            cols - step_width,
        )

        delta = -step_width

    row = 0

    while row < rows:

        if col < 0 or col >= cols:
            break

        span_c = min(
            step_width,
            cols - col,
        )

        span_r = min(
            step_height,
            rows - row,
        )

        if (
            span_c > 0
            and
            span_r > 0
        ):

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

        row += step_height
        col += delta


# ============================================================
# 30. LARGE BLOCK — STEPPED MASS
# ============================================================

def motif_stepped_mass(
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

    if (
        cols < 3
        or
        rows < 3
    ):
        return

    settings = dict(
        settings
    )

    settings["gradient"] = (
        random.random()
        <
        0.12
    )

    mirror = (
        random.random() < 0.5
    )

    max_width = cols

    for row in range(rows):

        step = (
            row // 2
        )

        span = max(
            1,
            max_width - step,
        )

        if mirror:

            start_col = (
                max_width - span
            )

        else:

            start_col = 0

        if start_col >= cols:
            continue

        span = min(
            span,
            cols - start_col,
        )

        render_shape(
            canvas,
            cell_box(
                region,
                row,
                start_col,
                small_unit,
                span_c=span,
            ),
            "rect",
            row,
            start_col,
            rows,
            cols,
            settings,
            splice_mask,
            region,
        )


# ============================================================
# 31. MOTIF WEIGHTS
# ============================================================

VITAL_MOTIFS = [

    "lattice",
    "lattice",
    "lattice",

    "cellular_cross",
    "cellular_cross",

    "vertebra",
    "vertebra",

    "offset_chain",

    "capsules",
    "capsules",
]


SUPPORT_MOTIFS = [

    "diamonds",
    "checker",
]


LARGE_MOTIFS = [

    "large_block",
    "large_block",

    "stair_block",
    "stair_block",
    "stair_block",

    "stepped_mass",
]


def choose_motif():

    if (
        random.random()
        <
        LARGE_BLOCK_PROBABILITY
    ):

        return random.choice(
            LARGE_MOTIFS
        )

    if (
        random.random()
        <
        VITAL_MOTIF_WEIGHT
    ):

        return random.choice(
            VITAL_MOTIFS
        )

    return random.choice(
        SUPPORT_MOTIFS
    )


# ============================================================
# 32. MOTIF DISPATCH
# ============================================================

def render_motif(
    canvas,
    region,
    motif,
    small_unit,
    settings,
    splice_mask,
):

    if motif == "cellular_cross":

        motif_cellular_cross(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "lattice":

        motif_lattice(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "vertebra":

        motif_vertebra(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "offset_chain":

        motif_offset_chain(
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

    elif motif == "diamonds":

        motif_diamonds(
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

    elif motif == "large_block":

        motif_large_block(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "stair_block":

        motif_stair_block(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )

    elif motif == "stepped_mass":

        motif_stepped_mass(
            canvas,
            region,
            small_unit,
            settings,
            splice_mask,
        )


# ============================================================
# 33. MACRO PATCHWORK
# ============================================================

def build_macro_regions(
    width,
    height,
    large_unit,
):

    cols = int(
        math.ceil(
            width
            / large_unit
        )
    )

    rows = int(
        math.ceil(
            height
            / large_unit
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

        start_r, start_c = empty[
            random.randrange(
                len(empty)
            )
        ]

        if random.random() < 0.5:

            span_c = random.choice(
                [
                    1,
                    2,
                    2,
                    3,
                ]
            )

            span_r = random.choice(
                [
                    1,
                    1,
                    2,
                ]
            )

        else:

            span_c = random.choice(
                [
                    1,
                    1,
                    2,
                ]
            )

            span_r = random.choice(
                [
                    1,
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

        regions.append(
            (
                start_c
                * large_unit,

                start_r
                * large_unit,

                min(
                    width,
                    end_c
                    * large_unit,
                ),

                min(
                    height,
                    end_r
                    * large_unit,
                ),
            )
        )

    return regions


# ============================================================
# 34. CREAM PAPER
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
        0.18,
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
# 35. QUIET OVERPRINT
# ============================================================

def add_overprint(
    canvas,
    width,
    height,
    small_unit,
):

    if random.random() > 0.30:
        return

    family = random.choice(
        [
            "green",
            "blue",
            "berry",
            "olive",
        ]
    )

    color = palette_color(
        family,
        random.choice(
            [
                1,
                2,
                3,
            ]
        ),
    )

    color = apply_vital_mood_bias(
        color,
        1.0,
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

    horizontal = (
        random.random()
        <
        0.5
    )

    stripe_count = random.randint(
        2,
        4,
    )

    if horizontal:

        max_rows = max(
            1,
            height // small_unit,
        )

        start = random.randint(
            0,
            max_rows - 1,
        )

        for i in range(
            stripe_count
        ):

            row = (
                start + i * 2
            ) % max_rows

            y0 = hi(
                row * small_unit
            )

            y1 = hi(
                (
                    row + 1
                )
                * small_unit
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
                        6,
                        15,
                    ),
                ),
            )

    else:

        max_cols = max(
            1,
            width // small_unit,
        )

        start = random.randint(
            0,
            max_cols - 1,
        )

        for i in range(
            stripe_count
        ):

            col = (
                start + i * 2
            ) % max_cols

            x0 = hi(
                col * small_unit
            )

            x1 = hi(
                (
                    col + 1
                )
                * small_unit
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
                        6,
                        15,
                    ),
                ),
            )

    canvas.alpha_composite(
        overlay
    )


# ============================================================
# 36. FINAL PRINT GRAIN
# ============================================================

def apply_print_texture(image):

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
# 37. MAIN GENERATOR
# ============================================================

def generate_vital_edge_pattern(
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
    # GLOBAL SPLICE
    # --------------------------------------------------------

    splice_direction = random.choice(
        [
            "down",
            "up",
        ]
    )

    splice_position = random.uniform(
        0.24,
        0.72,
    )

    splice_mask = create_splice_mask(
        width,
        height,
        small_unit,
        splice_direction,
        splice_position,
    )

    # --------------------------------------------------------
    # PATCHWORK
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
    large_regions = 0

    for region in regions:

        # ----------------------------------------------------
        # Motif continuity
        # ----------------------------------------------------

        if (
            previous_motif is not None
            and random.random() < 0.42
            and previous_motif not in LARGE_MOTIFS
        ):

            motif = previous_motif

        else:

            motif = choose_motif()

        # ----------------------------------------------------
        # Color continuity
        # ----------------------------------------------------

        if (
            previous_settings is not None
            and random.random() < 0.24
        ):

            settings = dict(
                previous_settings
            )

            settings[
                "shimmer_phase"
            ] += random.uniform(
                -0.45,
                0.45,
            )

        else:

            settings = create_region_settings(
                previous_settings
            )

        if settings["gradient"]:
            gradient_regions += 1

        if settings["shimmer"]:
            shimmer_regions += 1

        if settings["splice"]:
            splice_regions += 1

        if motif in LARGE_MOTIFS:
            large_regions += 1

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
    # Restrained overprint
    # --------------------------------------------------------

    add_overprint(
        canvas,
        width,
        height,
        small_unit,
    )

    # --------------------------------------------------------
    # Downsample once
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

        "large_regions":
            large_regions,

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
# 38. LOCAL VS CODE RUNNER
# ============================================================

if __name__ == "__main__":

    art, info = generate_vital_edge_pattern(
        OUTPUT_WIDTH,
        OUTPUT_HEIGHT,
    )

    output_id = random.randint(
        0,
        999_999_999,
    )

    filename = (
        f"vital_edge_pattern_v3_"
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
        " VITAL EDGE PATTERN v3 GENERATED"
    )

    print(
        "======================================"
    )

    print(
        f" Seed:             {info['seed']}"
    )

    print(
        f" Size:             "
        f"{OUTPUT_WIDTH} x {OUTPUT_HEIGHT}"
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
        f" Large anchors:    "
        f"{info['large_regions']}"
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