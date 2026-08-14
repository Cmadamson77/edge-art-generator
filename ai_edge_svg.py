import html
import math
import random


# ============================================================
# AI EDGE SVG GENERATOR v1
# ============================================================
#
# Parallel VECTOR renderer for the approved AI Edge system.
#
# IMPORTANT:
#
# - Does NOT modify or replace the Pillow PNG generator.
# - Generates a new AI Edge composition using the same
#   visual rules and palette logic.
# - Native SVG shapes.
# - Native vector gradients.
# - No grain.
# - Grid locked.
# - Organized groups for Illustrator / After Effects.
#
# Main function:
#
#     generate_ai_edge_svg(width, height)
#
# Returns:
#
#     svg_string, metadata
#
# ============================================================


# ============================================================
# 1. SETTINGS
# ============================================================

PAPER = "#EAE7D9"

OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1600

TRUE_GRADIENT_REGION_PROBABILITY = 0.36
SHIMMER_REGION_PROBABILITY = 0.58
SPLICE_REGION_PROBABILITY = 0.66

AI_MOTIF_WEIGHT = 0.70


# ============================================================
# 2. AI EDGE PALETTE
# ============================================================

PALETTE = {

    "orange": [
        "#753C0F",
        "#AE5D1E",
        "#FF5B00",
        "#FF7E36",
        "#FFB96E",
        "#FFD4A7",
    ],

    "blue": [
        "#173736",
        "#2C615F",
        "#449491",
        "#6BB3B0",
        "#98C2C0",
        "#CFD4D3",
    ],

    "red": [
        "#410F13",
        "#740912",
        "#FF0015",
        "#FF4D5B",
        "#FFBAB9",
        "#FDDCDC",
    ],

    "purple": [
        "#150833",
        "#36265A",
        "#A92CFF",
        "#EBC2F5",
        "#F9E3FF",
        "#F9E3FF",
    ],
}


# ============================================================
# 3. APPROVED AI GRADIENT PAIRINGS
# ============================================================

AI_GRADIENTS = [

    (
        "#FFD4A7",
        "#FF0015",
    ),

    (
        "#EBC2F5",
        "#740912",
    ),

    (
        "#753C0F",
        "#A92CFF",
    ),

    (
        "#CFD4D3",
        "#449491",
    ),
]


# ============================================================
# 4. HELPERS
# ============================================================

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


def rgb_to_hex(color):

    return "#{:02X}{:02X}{:02X}".format(
        int(clamp(color[0], 0, 255)),
        int(clamp(color[1], 0, 255)),
        int(clamp(color[2], 0, 255)),
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
            * (1.0 - t)
            +
            color_b[i]
            * t
        )
        for i in range(3)
    )


def family_color(
    family,
    t,
):

    colors = PALETTE[
        family
    ]

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

    rgb = mix_rgb(
        hex_to_rgb(
            colors[left]
        ),
        hex_to_rgb(
            colors[right]
        ),
        local_t,
    )

    return rgb_to_hex(
        rgb
    )


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


# ============================================================
# 5. GRID
# ============================================================

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
        for d in divisors(
            common
        )
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
            key=lambda d:
            abs(
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
# 6. SVG UTILITY
# ============================================================

def attr_string(**attrs):

    parts = []

    for key, value in attrs.items():

        if value is None:
            continue

        key = key.replace(
            "_",
            "-",
        )

        parts.append(
            f'{key}="{html.escape(str(value))}"'
        )

    return " ".join(
        parts
    )


def svg_rect(
    x,
    y,
    width,
    height,
    fill,
    rx=None,
    opacity=None,
):

    return (
        "<rect "
        +
        attr_string(
            x=x,
            y=y,
            width=width,
            height=height,
            fill=fill,
            rx=rx,
            opacity=opacity,
        )
        +
        " />"
    )


def svg_circle(
    cx,
    cy,
    r,
    fill,
    opacity=None,
):

    return (
        "<circle "
        +
        attr_string(
            cx=cx,
            cy=cy,
            r=r,
            fill=fill,
            opacity=opacity,
        )
        +
        " />"
    )


def svg_polygon(
    points,
    fill,
    opacity=None,
):

    value = " ".join(
        f"{x},{y}"
        for x, y in points
    )

    return (
        "<polygon "
        +
        attr_string(
            points=value,
            fill=fill,
            opacity=opacity,
        )
        +
        " />"
    )


# ============================================================
# 7. SHAPE RECORDS
# ============================================================
#
# Instead of immediately rendering, motif functions create
# vector shape records.
#
# That allows the same shape set to be used for:
#
# - primary motif
# - splice
# - shimmer
#
# ============================================================

def shape_record(
    shape,
    bbox,
    row,
    col,
    rows,
    cols,
):

    return {
        "shape": shape,
        "bbox": bbox,
        "row": row,
        "col": col,
        "rows": rows,
        "cols": cols,
    }


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
            col
            +
            span_c
        )
        *
        small_unit,

        y0
        +
        (
            row
            +
            span_r
        )
        *
        small_unit,
    )


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


# ============================================================
# 8. SHAPE -> SVG
# ============================================================

def render_shape_svg(
    record,
    fill,
    opacity=0.94,
):

    shape = record[
        "shape"
    ]

    x0, y0, x1, y1 = record[
        "bbox"
    ]

    width = (
        x1 - x0
    )

    height = (
        y1 - y0
    )

    if shape == "circle":

        size = min(
            width,
            height,
        )

        cx = (
            x0
            +
            width / 2
        )

        cy = (
            y0
            +
            height / 2
        )

        return svg_circle(
            cx,
            cy,
            size / 2,
            fill,
            opacity,
        )

    if shape == "diamond":

        cx = (
            x0
            +
            width / 2
        )

        cy = (
            y0
            +
            height / 2
        )

        return svg_polygon(
            [
                (
                    cx,
                    y0,
                ),
                (
                    x1,
                    cy,
                ),
                (
                    cx,
                    y1,
                ),
                (
                    x0,
                    cy,
                ),
            ],
            fill,
            opacity,
        )

    if shape == "triangle_up":

        return svg_polygon(
            [
                (
                    x0
                    +
                    width / 2,
                    y0,
                ),
                (
                    x1,
                    y1,
                ),
                (
                    x0,
                    y1,
                ),
            ],
            fill,
            opacity,
        )

    if shape == "triangle_down":

        return svg_polygon(
            [
                (
                    x0,
                    y0,
                ),
                (
                    x1,
                    y0,
                ),
                (
                    x0
                    +
                    width / 2,
                    y1,
                ),
            ],
            fill,
            opacity,
        )

    if shape == "capsule":

        radius = (
            min(
                width,
                height,
            )
            /
            2
        )

        return svg_rect(
            x0,
            y0,
            width,
            height,
            fill,
            rx=radius,
            opacity=opacity,
        )

    return svg_rect(
        x0,
        y0,
        width,
        height,
        fill,
        opacity=opacity,
    )


# ============================================================
# 9. MACRO REGIONS
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

    occupied = [
        [
            False
            for _ in range(cols)
        ]
        for _ in range(rows)
    ]

    regions = []

    attempts = 0

    while attempts < 800:

        attempts += 1

        empty = []

        for r in range(rows):
            for c in range(cols):

                if not occupied[r][c]:
                    empty.append(
                        (
                            r,
                            c,
                        )
                    )

        if not empty:
            break

        start_r, start_c = random.choice(
            empty
        )

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
            start_c
            +
            span_c,
        )

        end_r = min(
            rows,
            start_r
            +
            span_r,
        )

        collision = False

        for r in range(
            start_r,
            end_r,
        ):

            for c in range(
                start_c,
                end_c,
            ):

                if occupied[r][c]:
                    collision = True

        if collision:
            continue

        for r in range(
            start_r,
            end_r,
        ):

            for c in range(
                start_c,
                end_c,
            ):

                occupied[r][c] = True

        regions.append(
            (
                start_c
                *
                large_unit,

                start_r
                *
                large_unit,

                min(
                    width,
                    end_c
                    *
                    large_unit,
                ),

                min(
                    height,
                    end_r
                    *
                    large_unit,
                ),
            )
        )

    return regions


# ============================================================
# 10. REGION COLOR SETTINGS
# ============================================================

def choose_splice_color(
    family,
):

    options = [
        f
        for f in PALETTE
        if f != family
    ]

    other = random.choice(
        options
    )

    index = random.choice(
        [
            0,
            1,
            1,
            2,
        ]
    )

    return PALETTE[
        other
    ][index]


def create_region_settings():

    family = random.choice(
        list(
            PALETTE.keys()
        )
    )

    return {

        "family":
            family,

        "gradient":
            (
                random.random()
                <
                TRUE_GRADIENT_REGION_PROBABILITY
            ),

        "gradient_pair":
            random.choice(
                AI_GRADIENTS
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
            (
                random.random()
                <
                SHIMMER_REGION_PROBABILITY
            ),

        "splice":
            (
                random.random()
                <
                SPLICE_REGION_PROBABILITY
            ),

        "splice_color":
            choose_splice_color(
                family
            ),
    }


# ============================================================
# 11. MOTIFS
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


def motif_factory(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    if rows < 3:
        return shapes

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

        shapes.append(
            shape_record(
                "triangle_up",
                cell_box(
                    region,
                    roof_row,
                    col,
                    small_unit,
                ),
                roof_row,
                col,
                rows,
                cols,
            )
        )

        shapes.append(
            shape_record(
                "rect",
                cell_box(
                    region,
                    roof_row,
                    col + 1,
                    small_unit,
                ),
                roof_row,
                col + 1,
                rows,
                cols,
            )
        )

    for row in range(
        roof_row + 1,
        rows,
    ):

        for col in range(
            cols
        ):

            shapes.append(
                shape_record(
                    "rect",
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                    ),
                    row,
                    col,
                    rows,
                    cols,
                )
            )

    return shapes


def motif_ladder(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    if cols < 3:
        return shapes

    spine = cols // 2

    for row in range(rows):

        shapes.append(
            shape_record(
                "rect",
                cell_box(
                    region,
                    row,
                    spine,
                    small_unit,
                ),
                row,
                spine,
                rows,
                cols,
            )
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

            shapes.append(
                shape_record(
                    "rect",
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                    ),
                    row,
                    col,
                    rows,
                    cols,
                )
            )

    return shapes


def motif_staggered(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    row = 0

    while row < rows:

        offset = (
            row % 4
        ) // 2

        col = offset

        while col < cols:

            span_c = min(
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

            span_r = min(
                random.choice(
                    [
                        1,
                        1,
                        2,
                    ]
                ),
                rows - row,
            )

            shapes.append(
                shape_record(
                    "rect",
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                        span_c,
                        span_r,
                    ),
                    row,
                    col,
                    rows,
                    cols,
                )
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

    return shapes


def motif_circles(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    return [
        shape_record(
            "circle",
            cell_box(
                region,
                row,
                col,
                small_unit,
            ),
            row,
            col,
            rows,
            cols,
        )
        for row in range(rows)
        for col in range(cols)
    ]


def motif_diamonds(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    return [
        shape_record(
            "diamond",
            cell_box(
                region,
                row,
                col,
                small_unit,
            ),
            row,
            col,
            rows,
            cols,
        )
        for row in range(rows)
        for col in range(cols)
    ]


def motif_capsules(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

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

                shapes.append(
                    shape_record(
                        "capsule",
                        cell_box(
                            region,
                            row,
                            col,
                            small_unit,
                            span_c=span,
                        ),
                        row,
                        col,
                        rows,
                        cols,
                    )
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

                shapes.append(
                    shape_record(
                        "capsule",
                        cell_box(
                            region,
                            row,
                            col,
                            small_unit,
                            span_r=span,
                        ),
                        row,
                        col,
                        rows,
                        cols,
                    )
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

    return shapes


def motif_checker(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    for row in range(rows):

        for col in range(cols):

            if (
                row + col
            ) % 2 == 0:

                shapes.append(
                    shape_record(
                        "rect",
                        cell_box(
                            region,
                            row,
                            col,
                            small_unit,
                        ),
                        row,
                        col,
                        rows,
                        cols,
                    )
                )

    return shapes


def motif_woven(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    for row in range(rows):

        if row % 2 == 0:

            col = 0

            while col < cols:

                span = min(
                    2,
                    cols - col,
                )

                shapes.append(
                    shape_record(
                        "rect",
                        cell_box(
                            region,
                            row,
                            col,
                            small_unit,
                            span_c=span,
                        ),
                        row,
                        col,
                        rows,
                        cols,
                    )
                )

                col += 3

        else:

            for col in range(
                1,
                cols,
                3,
            ):

                shapes.append(
                    shape_record(
                        "rect",
                        cell_box(
                            region,
                            row,
                            col,
                            small_unit,
                        ),
                        row,
                        col,
                        rows,
                        cols,
                    )
                )

    return shapes


def build_motif_shapes(
    motif,
    region,
    small_unit,
):

    if motif == "factory":
        return motif_factory(
            region,
            small_unit,
        )

    if motif == "ladder":
        return motif_ladder(
            region,
            small_unit,
        )

    if motif == "staggered":
        return motif_staggered(
            region,
            small_unit,
        )

    if motif == "circles":
        return motif_circles(
            region,
            small_unit,
        )

    if motif == "diamonds":
        return motif_diamonds(
            region,
            small_unit,
        )

    if motif == "capsules":
        return motif_capsules(
            region,
            small_unit,
        )

    if motif == "checker":
        return motif_checker(
            region,
            small_unit,
        )

    return motif_woven(
        region,
        small_unit,
    )


# ============================================================
# 12. SOLID COLOR POSITION
# ============================================================

def shape_t(
    record,
    axis,
):

    row = record[
        "row"
    ]

    col = record[
        "col"
    ]

    rows = record[
        "rows"
    ]

    cols = record[
        "cols"
    ]

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

    return (
        row + col
    ) / max(
        1,
        rows + cols - 2,
    )


# ============================================================
# 13. GLOBAL SPLICE GEOMETRY
# ============================================================

def splice_polygons(
    width,
    height,
    small_unit,
    direction,
    position,
):

    margin = (
        width
        +
        height
        +
        small_unit
        *
        4
    )

    span = (
        width + height
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

        line_left = (
            0,
            b,
        )

        line_right = (
            width,
            width + b,
        )

        primary = [
            line_left,
            line_right,
            (
                width,
                height + margin,
            ),
            (
                0,
                height + margin,
            ),
        ]

        splice = [
            (
                0,
                -margin,
            ),
            (
                width,
                -margin,
            ),
            line_right,
            line_left,
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

        line_left = (
            0,
            b,
        )

        line_right = (
            width,
            b - width,
        )

        primary = [
            (
                0,
                -margin,
            ),
            (
                width,
                -margin,
            ),
            line_right,
            line_left,
        ]

        splice = [
            line_left,
            line_right,
            (
                width,
                height + margin,
            ),
            (
                0,
                height + margin,
            ),
        ]

    return (
        primary,
        splice,
    )


# ============================================================
# 14. REGION GRADIENT DEFINITION
# ============================================================

def gradient_definition(
    gradient_id,
    region,
    pair,
    axis,
):

    x0, y0, x1, y1 = region

    if axis == "y":

        points = (
            x0,
            y0,
            x0,
            y1,
        )

    elif axis == "diag_down":

        points = (
            x0,
            y0,
            x1,
            y1,
        )

    else:

        points = (
            x0,
            y0,
            x1,
            y0,
        )

    gx1, gy1, gx2, gy2 = points

    return f"""
    <linearGradient
        id="{gradient_id}"
        gradientUnits="userSpaceOnUse"
        x1="{gx1}"
        y1="{gy1}"
        x2="{gx2}"
        y2="{gy2}">
        <stop offset="0%" stop-color="{pair[0]}" />
        <stop offset="100%" stop-color="{pair[1]}" />
    </linearGradient>
    """


# ============================================================
# 15. SHIMMER DEFINITION
# ============================================================
#
# No grain.
#
# This is a clean vector tonal sweep intended to remain
# editable or removable in Illustrator / AE.
#
# ============================================================

def shimmer_definition(
    shimmer_id,
    region,
    axis,
):

    x0, y0, x1, y1 = region

    if axis == "y":

        points = (
            x0,
            y0,
            x0,
            y1,
        )

    else:

        points = (
            x0,
            y0,
            x1,
            y0,
        )

    sx1, sy1, sx2, sy2 = points

    return f"""
    <linearGradient
        id="{shimmer_id}"
        gradientUnits="userSpaceOnUse"
        x1="{sx1}"
        y1="{sy1}"
        x2="{sx2}"
        y2="{sy2}">
        <stop
            offset="0%"
            stop-color="#FFFFFF"
            stop-opacity="0"
        />
        <stop
            offset="42%"
            stop-color="#FFFFFF"
            stop-opacity="0"
        />
        <stop
            offset="52%"
            stop-color="#FFFFFF"
            stop-opacity="0.26"
        />
        <stop
            offset="62%"
            stop-color="#FFFFFF"
            stop-opacity="0"
        />
        <stop
            offset="100%"
            stop-color="#FFFFFF"
            stop-opacity="0"
        />
    </linearGradient>
    """


# ============================================================
# 16. OVERPRINT
# ============================================================

def create_overprint(
    width,
    height,
    small_unit,
):

    if random.random() > 0.42:
        return []

    family = random.choice(
        list(
            PALETTE.keys()
        )
    )

    color = random.choice(
        PALETTE[
            family
        ][1:4]
    )

    direction = random.choice(
        [
            "horizontal",
            "vertical",
        ]
    )

    count = random.randint(
        2,
        4,
    )

    items = []

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

        for i in range(count):

            row = (
                start
                +
                i * 2
            ) % max_rows

            items.append(
                svg_rect(
                    0,
                    row
                    *
                    small_unit,
                    width,
                    small_unit,
                    color,
                    opacity=0.055,
                )
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

        for i in range(count):

            col = (
                start
                +
                i * 2
            ) % max_cols

            items.append(
                svg_rect(
                    col
                    *
                    small_unit,
                    0,
                    small_unit,
                    height,
                    color,
                    opacity=0.055,
                )
            )

    return items


# ============================================================
# 17. MAIN SVG GENERATOR
# ============================================================

def generate_ai_edge_svg(
    width,
    height,
    seed=None,
):

    if seed is None:

        seed = random.randint(
            0,
            999_999_999,
        )

    random.seed(
        seed
    )

    (
        large_unit,
        small_unit,
        subdivision,
    ) = choose_grid(
        width,
        height,
    )

    regions = build_macro_regions(
        width,
        height,
        large_unit,
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
        0.69,
    )

    (
        primary_polygon,
        splice_polygon,
    ) = splice_polygons(
        width,
        height,
        small_unit,
        splice_direction,
        splice_position,
    )

    primary_clip_id = (
        "global-splice-primary"
    )

    splice_clip_id = (
        "global-splice-secondary"
    )

    # --------------------------------------------------------
    # SVG DEFINITIONS
    # --------------------------------------------------------

    defs = []

    primary_points = " ".join(
        f"{x},{y}"
        for x, y in primary_polygon
    )

    secondary_points = " ".join(
        f"{x},{y}"
        for x, y in splice_polygon
    )

    defs.append(
        f"""
        <clipPath id="{primary_clip_id}">
            <polygon points="{primary_points}" />
        </clipPath>
        """
    )

    defs.append(
        f"""
        <clipPath id="{splice_clip_id}">
            <polygon points="{secondary_points}" />
        </clipPath>
        """
    )

    # --------------------------------------------------------
    # REGION GENERATION
    # --------------------------------------------------------

    region_groups = []

    previous_motif = None
    previous_settings = None

    gradient_regions = 0
    shimmer_regions = 0
    splice_regions = 0

    for index, region in enumerate(
        regions,
        start=1,
    ):

        region_id = (
            f"region-{index:03d}"
        )

        # ----------------------------------------------------
        # REPEAT MOTIFS
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
        # REPEAT COLOR LANGUAGE OCCASIONALLY
        # ----------------------------------------------------

        if (
            previous_settings is not None
            and
            random.random() < 0.28
        ):

            settings = dict(
                previous_settings
            )

        else:

            settings = create_region_settings()

        shapes = build_motif_shapes(
            motif,
            region,
            small_unit,
        )

        if not shapes:
            continue

        # ----------------------------------------------------
        # PRIMARY FILL
        # ----------------------------------------------------

        if settings[
            "gradient"
        ]:

            gradient_regions += 1

            gradient_id = (
                f"{region_id}-gradient"
            )

            defs.append(
                gradient_definition(
                    gradient_id,
                    region,
                    settings[
                        "gradient_pair"
                    ],
                    settings[
                        "gradient_axis"
                    ],
                )
            )

            primary_fills = [
                f"url(#{gradient_id})"
                for _ in shapes
            ]

        else:

            primary_fills = []

            for shape in shapes:

                t = shape_t(
                    shape,
                    settings[
                        "gradient_axis"
                    ],
                )

                primary_fills.append(
                    family_color(
                        settings[
                            "family"
                        ],
                        t,
                    )
                )

        # ----------------------------------------------------
        # BUILD PRIMARY MOTIF
        # ----------------------------------------------------

        primary_shapes = []

        for shape, fill in zip(
            shapes,
            primary_fills,
        ):

            primary_shapes.append(
                render_shape_svg(
                    shape,
                    fill,
                )
            )

        motif_group = (
            f"""
            <g id="{region_id}-motif">
                {''.join(primary_shapes)}
            </g>
            """
        )

        # ----------------------------------------------------
        # SPLICE
        # ----------------------------------------------------

        splice_group = ""

        if settings[
            "splice"
        ]:

            splice_regions += 1

            primary_clipped = []

            splice_shapes = []

            for shape, fill in zip(
                shapes,
                primary_fills,
            ):

                primary_clipped.append(
                    render_shape_svg(
                        shape,
                        fill,
                    )
                )

                splice_shapes.append(
                    render_shape_svg(
                        shape,
                        settings[
                            "splice_color"
                        ],
                    )
                )

            motif_group = (
                f"""
                <g
                    id="{region_id}-motif"
                    clip-path="url(#{primary_clip_id})">
                    {''.join(primary_clipped)}
                </g>
                """
            )

            splice_group = (
                f"""
                <g
                    id="{region_id}-splice"
                    clip-path="url(#{splice_clip_id})">
                    {''.join(splice_shapes)}
                </g>
                """
            )

        # ----------------------------------------------------
        # SHIMMER
        # ----------------------------------------------------

        shimmer_group = ""

        if settings[
            "shimmer"
        ]:

            shimmer_regions += 1

            shimmer_id = (
                f"{region_id}-shimmer-gradient"
            )

            defs.append(
                shimmer_definition(
                    shimmer_id,
                    region,
                    settings[
                        "gradient_axis"
                    ],
                )
            )

            shimmer_shapes = []

            for shape in shapes:

                shimmer_shapes.append(
                    render_shape_svg(
                        shape,
                        f"url(#{shimmer_id})",
                        opacity=0.50,
                    )
                )

            shimmer_group = (
                f"""
                <g
                    id="{region_id}-shimmer"
                    opacity="0.45">
                    {''.join(shimmer_shapes)}
                </g>
                """
            )

        # ----------------------------------------------------
        # WRAP REGION
        # ----------------------------------------------------

        region_groups.append(
            f"""
            <g
                id="{region_id}"
                data-motif="{motif}"
                data-family="{settings['family']}"
                data-gradient="{str(settings['gradient']).lower()}"
                data-splice="{str(settings['splice']).lower()}"
                data-shimmer="{str(settings['shimmer']).lower()}">

                {motif_group}

                {splice_group}

                {shimmer_group}

            </g>
            """
        )

        previous_motif = motif
        previous_settings = settings

    # --------------------------------------------------------
    # OVERPRINT
    # --------------------------------------------------------

    overprint_items = create_overprint(
        width,
        height,
        small_unit,
    )

    # --------------------------------------------------------
    # FINAL SVG
    # --------------------------------------------------------

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}">

    <title>AI Edge Pattern</title>

    <desc>
        AI Edge vector pattern.
        Seed: {seed}.
        Grid: {small_unit}px.
        Generated as editable SVG geometry.
    </desc>

    <defs>
        {''.join(defs)}
    </defs>

    <!-- ================================================ -->
    <!-- BACKGROUND                                       -->
    <!-- ================================================ -->

    <g id="background">
        <rect
            x="0"
            y="0"
            width="{width}"
            height="{height}"
            fill="{PAPER}"
        />
    </g>


    <!-- ================================================ -->
    <!-- MACRO REGIONS                                    -->
    <!-- ================================================ -->

    <g id="macro-regions">
        {''.join(region_groups)}
    </g>


    <!-- ================================================ -->
    <!-- OVERPRINT                                        -->
    <!-- ================================================ -->

    <g id="overprint">
        {''.join(overprint_items)}
    </g>

</svg>
"""

    metadata = {

        "seed":
            seed,

        "width":
            width,

        "height":
            height,

        "small_unit":
            small_unit,

        "large_unit":
            large_unit,

        "subdivision":
            subdivision,

        "region_count":
            len(region_groups),

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
        svg,
        metadata,
    )


# ============================================================
# 18. LOCAL VS CODE RUNNER
# ============================================================

if __name__ == "__main__":

    svg, info = generate_ai_edge_svg(
        OUTPUT_WIDTH,
        OUTPUT_HEIGHT,
    )

    output_id = random.randint(
        0,
        999_999_999,
    )

    filename = (
        f"ai_edge_pattern_svg_"
        f"{output_id}.svg"
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            svg
        )

    print()

    print(
        "======================================"
    )

    print(
        " AI EDGE SVG GENERATED"
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
        f"{info['width']} x "
        f"{info['height']}"
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
        f" Gradient regions: "
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
        f" File:             "
        f"{filename}"
    )

    print(
        "======================================"
    )