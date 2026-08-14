import html
import math
import random


# ============================================================
# VITAL EDGE SVG GENERATOR v1
# ============================================================
#
# Parallel VECTOR renderer for the approved Vital Edge V3
# visual system.
#
# IMPORTANT:
#
# - Does NOT modify the Pillow PNG generator.
# - Native SVG geometry.
# - Native vector gradients.
# - No grain.
# - Cream ground.
# - Grid locked.
# - Moodier / earthier Vital color bias.
# - Vital motifs dominate:
#       lattice
#       cellular cross
#       vertebra
#       offset chain
#       capsules
# - Includes larger architectural blocks / stair-step masses.
# - Organized SVG groups for Illustrator / After Effects.
#
# Main function:
#
#     generate_vital_edge_svg(width, height)
#
# Returns:
#
#     svg_string, metadata
#
# ============================================================


# ============================================================
# 1. GLOBAL SETTINGS
# ============================================================

PAPER = "#EAE7D9"

OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = 1600

LARGE_BLOCK_PROBABILITY = 0.27

TRUE_GRADIENT_REGION_PROBABILITY = 0.34
SHIMMER_REGION_PROBABILITY = 0.52
SPLICE_REGION_PROBABILITY = 0.58

VITAL_MOTIF_WEIGHT = 0.78

HIGH_CHROMA_ACCENT_PROBABILITY = 0.065


# ============================================================
# 2. VITAL EDGE PALETTE
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
# 3. CURATED VITAL TRUE GRADIENTS
# ============================================================

VITAL_GRADIENTS = [

    (
        "#173A17",
        "#98AF58",
    ),

    (
        "#153B91",
        "#D7E0F0",
    ),

    (
        "#52082F",
        "#E98BB3",
    ),

    (
        "#20231F",
        "#B7B8A8",
    ),

    (
        "#A7BCE8",
        "#B7317F",
    ),

    (
        "#3F5E39",
        "#B8CC72",
    ),

    (
        "#100B2A",
        "#9BA48E",
    ),

    (
        "#7D184C",
        "#7396DA",
    ),

    (
        "#4F682D",
        "#D6D3C5",
    ),
]


ACCENT_COLORS = [
    "#D75591",
    "#7396DA",
    "#98AF58",
    "#B8CC72",
    "#B7317F",
]


# ============================================================
# 4. BASIC HELPERS
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


def divisors(number):

    values = []

    for i in range(
        1,
        int(math.sqrt(number)) + 1,
    ):

        if number % i == 0:

            values.append(i)

            if i != number // i:
                values.append(
                    number // i
                )

    return sorted(values)


# ============================================================
# 5. COLOR LOGIC
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


def family_color(
    family,
    t,
):

    colors = PALETTE[
        family
    ]

    t = clamp(
        t,
        0.0,
        1.0,
    )

    # Compress toward darker / middle values.
    t = (
        0.05
        +
        t * 0.70
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

    return PALETTE[
        family
    ][index]


def choose_accent_color():

    return random.choice(
        ACCENT_COLORS
    )


# ============================================================
# 6. GRID
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
                / 48
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
# 7. SVG UTILITY
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

    points_value = " ".join(
        f"{x},{y}"
        for x, y in points
    )

    return (
        "<polygon "
        +
        attr_string(
            points=points_value,
            fill=fill,
            opacity=opacity,
        )
        +
        " />"
    )


# ============================================================
# 8. GRID HELPERS
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
            // small_unit
        ),
    )

    rows = max(
        1,
        int(
            (
                y1 - y0
            )
            // small_unit
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
        col * small_unit,

        y0
        +
        row * small_unit,

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


# ============================================================
# 9. SHAPE RECORDS
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

        "shape":
            shape,

        "bbox":
            bbox,

        "row":
            row,

        "col":
            col,

        "rows":
            rows,

        "cols":
            cols,
    }


# ============================================================
# 10. VECTOR SHAPE RENDERER
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

        return svg_circle(
            x0 + width / 2,
            y0 + height / 2,
            size / 2,
            fill,
            opacity,
        )

    if shape == "diamond":

        cx = (
            x0 + width / 2
        )

        cy = (
            y0 + height / 2
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

    if shape == "capsule":

        return svg_rect(
            x0,
            y0,
            width,
            height,
            fill,
            rx=min(
                width,
                height,
            ) / 2,
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
# 11. MACRO REGION CONSTRUCTION
# ============================================================

def build_macro_regions(
    width,
    height,
    large_unit,
):

    cols = int(
        math.ceil(
            width / large_unit
        )
    )

    rows = int(
        math.ceil(
            height / large_unit
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

    while attempts < 900:

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
            start_c + span_c,
        )

        end_r = min(
            rows,
            start_r + span_r,
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
# 12. REGION SETTINGS
# ============================================================

def create_region_settings(
    previous_settings=None,
):

    family = choose_primary_family()

    # Neighbor rule:
    # if last region was high chroma,
    # steer immediately back to earthier tones.

    if (
        previous_settings is not None
        and
        previous_settings.get(
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

        "high_chroma":
            high_chroma,
    }


# ============================================================
# 13. VITAL MOTIF LISTS
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
# 14. MOTIF — CELLULAR CROSS
# ============================================================

def motif_cellular_cross(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

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

                    shapes.append(
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
                    )

    return shapes


# ============================================================
# 15. MOTIF — LATTICE
# ============================================================

def motif_lattice(
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
                row % 2 == 0
                or
                col % 2 == 0
            ):

                shapes.append(
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
                )

    return shapes


# ============================================================
# 16. MOTIF — VERTEBRA
# ============================================================

def motif_vertebra(
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

        # center spine
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

        # paired ribs
        if row % 2 == 0:

            span = random.choice(
                [
                    1,
                    1,
                    2,
                    2,
                    3,
                ]
            )

            for distance in range(
                1,
                span + 1,
            ):

                left = (
                    spine
                    -
                    distance
                )

                right = (
                    spine
                    +
                    distance
                )

                if left >= 0:

                    shapes.append(
                        shape_record(
                            "rect",
                            cell_box(
                                region,
                                row,
                                left,
                                small_unit,
                            ),
                            row,
                            left,
                            rows,
                            cols,
                        )
                    )

                if right < cols:

                    shapes.append(
                        shape_record(
                            "rect",
                            cell_box(
                                region,
                                row,
                                right,
                                small_unit,
                            ),
                            row,
                            right,
                            rows,
                            cols,
                        )
                    )

    return shapes


# ============================================================
# 17. MOTIF — OFFSET CHAIN
# ============================================================

def motif_offset_chain(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    if cols < 2:
        return shapes

    col = random.randint(
        0,
        max(
            0,
            cols - 1,
        ),
    )

    direction = random.choice(
        [
            -1,
            1,
        ]
    )

    for row in range(rows):

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

        if row % 2 == 1:

            col += direction

            if col <= 0:
                direction = 1

            if col >= cols - 1:
                direction = -1

            col = clamp(
                col,
                0,
                cols - 1,
            )

    return shapes


# ============================================================
# 18. MOTIF — CAPSULES
# ============================================================

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

                row += span

    return shapes


# ============================================================
# 19. MOTIF — DIAMONDS
# ============================================================

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


# ============================================================
# 20. MOTIF — CHECKER
# ============================================================

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


# ============================================================
# 21. LARGE MOTIF — BLOCK
# ============================================================

def motif_large_block(
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

            # restrained small holes
            if (
                random.random()
                <
                0.075
            ):
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


# ============================================================
# 22. LARGE MOTIF — STAIR BLOCK
# ============================================================

def motif_stair_block(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    if (
        cols < 2
        or
        rows < 2
    ):
        return shapes

    step_width = random.choice(
        [
            1,
            1,
            2,
        ]
    )

    step_height = random.choice(
        [
            1,
            1,
            2,
        ]
    )

    direction = random.choice(
        [
            "down_right",
            "down_left",
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

        if (
            col < 0
            or
            col >= cols
        ):
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

            shapes.append(
                shape_record(
                    "rect",
                    cell_box(
                        region,
                        row,
                        col,
                        small_unit,
                        span_c=span_c,
                        span_r=span_r,
                    ),
                    row,
                    col,
                    rows,
                    cols,
                )
            )

        row += step_height
        col += delta

    return shapes


# ============================================================
# 23. LARGE MOTIF — STEPPED MASS
# ============================================================

def motif_stepped_mass(
    region,
    small_unit,
):

    cols, rows = region_grid(
        region,
        small_unit,
    )

    shapes = []

    if (
        cols < 3
        or
        rows < 3
    ):

        return shapes

    mirror = (
        random.random()
        <
        0.5
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

        shapes.append(
            shape_record(
                "rect",
                cell_box(
                    region,
                    row,
                    start_col,
                    small_unit,
                    span_c=span,
                ),
                row,
                start_col,
                rows,
                cols,
            )
        )

    return shapes


# ============================================================
# 24. MOTIF DISPATCH
# ============================================================

def build_motif_shapes(
    motif,
    region,
    small_unit,
):

    if motif == "cellular_cross":

        return motif_cellular_cross(
            region,
            small_unit,
        )

    if motif == "lattice":

        return motif_lattice(
            region,
            small_unit,
        )

    if motif == "vertebra":

        return motif_vertebra(
            region,
            small_unit,
        )

    if motif == "offset_chain":

        return motif_offset_chain(
            region,
            small_unit,
        )

    if motif == "capsules":

        return motif_capsules(
            region,
            small_unit,
        )

    if motif == "diamonds":

        return motif_diamonds(
            region,
            small_unit,
        )

    if motif == "checker":

        return motif_checker(
            region,
            small_unit,
        )

    if motif == "large_block":

        return motif_large_block(
            region,
            small_unit,
        )

    if motif == "stair_block":

        return motif_stair_block(
            region,
            small_unit,
        )

    return motif_stepped_mass(
        region,
        small_unit,
    )


# ============================================================
# 25. POSITION / COLOR PROGRESSION
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
# 26. GLOBAL SPLICE
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
        small_unit * 4
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
# 27. SVG GRADIENT DEFINITION
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
        <stop
            offset="0%"
            stop-color="{pair[0]}"
        />
        <stop
            offset="100%"
            stop-color="{pair[1]}"
        />
    </linearGradient>
    """


# ============================================================
# 28. SVG SHIMMER DEFINITION
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
            offset="39%"
            stop-color="#FFFFFF"
            stop-opacity="0"
        />

        <stop
            offset="51%"
            stop-color="#FFFFFF"
            stop-opacity="0.22"
        />

        <stop
            offset="64%"
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
# 29. QUIET OVERPRINT
# ============================================================

def create_overprint(
    width,
    height,
    small_unit,
):

    if random.random() > 0.30:

        return []

    family = random.choice(
        [
            "green",
            "blue",
            "berry",
            "olive",
        ]
    )

    color = PALETTE[
        family
    ][
        random.choice(
            [
                1,
                2,
                3,
            ]
        )
    ]

    horizontal = (
        random.random()
        <
        0.5
    )

    stripe_count = random.randint(
        2,
        4,
    )

    items = []

    if horizontal:

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

            items.append(
                svg_rect(
                    0,
                    row
                    *
                    small_unit,
                    width,
                    small_unit,
                    color,
                    opacity=0.045,
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

        for i in range(
            stripe_count
        ):

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
                    opacity=0.045,
                )
            )

    return items


# ============================================================
# 30. MAIN SVG GENERATOR
# ============================================================

def generate_vital_edge_svg(
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
    large_regions = 0

    for index, region in enumerate(
        regions,
        start=1,
    ):

        region_id = (
            f"region-{index:03d}"
        )

        # ----------------------------------------------------
        # Controlled motif repetition
        # ----------------------------------------------------

        if (
            previous_motif is not None
            and
            random.random() < 0.44
        ):

            motif = previous_motif

        else:

            motif = choose_motif()

        # ----------------------------------------------------
        # Controlled color repetition
        # ----------------------------------------------------

        if (
            previous_settings is not None
            and
            random.random() < 0.24
        ):

            settings = dict(
                previous_settings
            )

            # Don't endlessly repeat bright areas.

            if settings.get(
                "high_chroma",
                False,
            ):

                settings = create_region_settings(
                    previous_settings
                )

        else:

            settings = create_region_settings(
                previous_settings
            )

        shapes = build_motif_shapes(
            motif,
            region,
            small_unit,
        )

        if not shapes:
            continue

        if motif in LARGE_MOTIFS:

            large_regions += 1

            # Approved V3 behavior:
            # large masses should mostly remain flat / architectural.

            settings = dict(
                settings
            )

            settings[
                "gradient"
            ] = (
                random.random()
                <
                0.12
            )

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

                fill = family_color(
                    settings[
                        "family"
                    ],
                    t,
                )

                # Extremely occasional brighter accent.
                if (
                    settings[
                        "high_chroma"
                    ]
                    and
                    random.random()
                    <
                    0.10
                ):

                    fill = (
                        choose_accent_color()
                    )

                primary_fills.append(
                    fill
                )

        # ----------------------------------------------------
        # PRIMARY MOTIF
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

            clipped_primary = []
            clipped_splice = []

            for shape, fill in zip(
                shapes,
                primary_fills,
            ):

                clipped_primary.append(
                    render_shape_svg(
                        shape,
                        fill,
                    )
                )

                clipped_splice.append(
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
                    {''.join(clipped_primary)}
                </g>
                """
            )

            splice_group = (
                f"""
                <g
                    id="{region_id}-splice"
                    clip-path="url(#{splice_clip_id})">
                    {''.join(clipped_splice)}
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
                        opacity=0.42,
                    )
                )

            shimmer_group = (
                f"""
                <g
                    id="{region_id}-shimmer"
                    opacity="0.42">
                    {''.join(shimmer_shapes)}
                </g>
                """
            )

        # ----------------------------------------------------
        # REGION WRAPPER
        # ----------------------------------------------------

        region_groups.append(
            f"""
            <g
                id="{region_id}"
                data-motif="{motif}"
                data-family="{settings['family']}"
                data-gradient="{str(settings['gradient']).lower()}"
                data-splice="{str(settings['splice']).lower()}"
                data-shimmer="{str(settings['shimmer']).lower()}"
                data-large="{str(motif in LARGE_MOTIFS).lower()}">

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

    <title>Vital Edge Pattern</title>

    <desc>
        Vital Edge vector pattern.
        Seed: {seed}.
        Grid: {small_unit}px.
        Generated as editable SVG geometry.
        Grain intentionally omitted.
    </desc>


    <!-- ================================================ -->
    <!-- DEFINITIONS                                      -->
    <!-- ================================================ -->

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
            len(
                region_groups
            ),

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
        svg,
        metadata,
    )


# ============================================================
# 31. LOCAL VS CODE RUNNER
# ============================================================

if __name__ == "__main__":

    svg, info = generate_vital_edge_svg(
        OUTPUT_WIDTH,
        OUTPUT_HEIGHT,
    )

    output_id = random.randint(
        0,
        999_999_999,
    )

    filename = (
        f"vital_edge_pattern_svg_"
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
        " VITAL EDGE SVG GENERATED"
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
        f" Large anchors:    "
        f"{info['large_regions']}"
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