import html
import math
import random


# ============================================================
# EDGE PRODUCTION VECTOR GENERATOR
# ============================================================
#
# CLEAN VECTOR EXPORT FOR:
#
#   - Adobe Illustrator
#   - Adobe After Effects
#
# This deliberately avoids:
#
#   - clipping masks
#   - nested region groups
#   - SVG filters
#   - duplicate shimmer overlays
#   - grain / raster texture
#
# Every visible object is written directly into the SVG.
#
# Small repeated primitives remain individual objects.
#
# Larger architectural shapes are consolidated where practical.
#
# True gradients remain editable SVG gradients.
#
# ============================================================


PAPER = "#EAE7D9"


# ============================================================
# 1. PALETTES
# ============================================================

AI_PALETTE = {
    "orange": [
        "#7D3E10",
        "#B6601D",
        "#FF6410",
        "#FF8136",
        "#FFB56A",
        "#FFD09B",
    ],

    "blue": [
        "#100B2A",
        "#123FC4",
        "#1657FF",
        "#7DA1EB",
        "#A8BFF0",
        "#D7E1F4",
    ],

    "red": [
        "#4D1115",
        "#8C1018",
        "#FF1721",
        "#FF515B",
        "#FFAAAA",
        "#F7D2D3",
    ],

    "purple": [
        "#1A0B37",
        "#3D2C63",
        "#A72AFF",
        "#D6A9E7",
        "#E8C7EF",
        "#F1DDF5",
    ],
}


VITAL_PALETTE = {
    "blue": [
        "#100B2A",
        "#123FC4",
        "#1657FF",
        "#7DA1EB",
        "#A8BFF0",
        "#D7E1F4",
    ],

    "green": [
        "#20231F",
        "#173A17",
        "#3F5E39",
        "#829B7C",
        "#A7B0A0",
        "#D0D0C4",
    ],

    "berry": [
        "#52082F",
        "#7D184C",
        "#B7317F",
        "#FF0A72",
        "#EF7EAF",
        "#F4CDDE",
    ],

    "olive": [
        "#293817",
        "#4F682D",
        "#91AD4D",
        "#B8CC72",
        "#D3F46A",
        "#EEF7D2",
    ],
}


AI_GRADIENTS = [
    ("#FFD09B", "#FF1721"),
    ("#D6A9E7", "#8C1018"),
    ("#7D3E10", "#A72AFF"),
    ("#A8BFF0", "#1657FF"),
    ("#100B2A", "#1657FF"),
    ("#4D1115", "#FF8136"),
]


VITAL_GRADIENTS = [
    ("#173A17", "#B8CC72"),
    ("#A8BFF0", "#1657FF"),
    ("#52082F", "#B7317F"),
    ("#20231F", "#A7B0A0"),
    ("#A8BFF0", "#B7317F"),
    ("#3F5E39", "#D3F46A"),
    ("#7D184C", "#7DA1EB"),
]


# ============================================================
# 2. FRANCHISE CONFIG
# ============================================================

CONFIG = {
    "AI Edge": {
        "prefix": "AI",
        "palette": AI_PALETTE,
        "gradients": AI_GRADIENTS,

        "family_weights": {
            "orange": 27,
            "blue": 27,
            "red": 26,
            "purple": 20,
        },

        "motifs": [
            "checker",
            "checker",
            "scaffold",
            "scaffold",
            "diamonds",
            "capsules",
            "saw_block",
            "saw_block",
            "stairs",
            "architectural",
        ],
    },

    "Vital Edge": {
        "prefix": "VITAL",
        "palette": VITAL_PALETTE,
        "gradients": VITAL_GRADIENTS,

        "family_weights": {
            "green": 36,
            "blue": 22,
            "berry": 18,
            "olive": 24,
        },

        "motifs": [
            "lattice",
            "lattice",
            "cellular",
            "cellular",
            "vertebra",
            "vertebra",
            "capsules",
            "checker",
            "stairs",
            "architectural",
        ],
    },
}


# ============================================================
# 3. HELPERS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def escape(value):
    return html.escape(str(value))


def hex_to_rgb(value):
    value = value.lstrip("#")

    return tuple(
        int(value[i:i + 2], 16)
        for i in (0, 2, 4)
    )


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(
        clamp(int(rgb[0]), 0, 255),
        clamp(int(rgb[1]), 0, 255),
        clamp(int(rgb[2]), 0, 255),
    )


def mix_colors(color_a, color_b, t):
    a = hex_to_rgb(color_a)
    b = hex_to_rgb(color_b)

    t = clamp(t, 0.0, 1.0)

    return rgb_to_hex(
        tuple(
            a[i] * (1 - t) + b[i] * t
            for i in range(3)
        )
    )


def choose_family(config):
    families = list(
        config["family_weights"].keys()
    )

    weights = [
        config["family_weights"][family]
        for family in families
    ]

    return random.choices(
        families,
        weights=weights,
        k=1,
    )[0]


def choose_family_color(
    config,
    family=None,
    bias="mid",
):

    if family is None:
        family = choose_family(config)

    colors = config["palette"][family]

    if bias == "dark":
        index = random.choices(
            [0, 1, 2, 3],
            weights=[20, 38, 30, 12],
            k=1,
        )[0]

    elif bias == "light":
        index = random.choices(
            [2, 3, 4, 5],
            weights=[10, 25, 38, 27],
            k=1,
        )[0]

    else:
        index = random.choices(
            range(len(colors)),
            weights=[10, 22, 30, 25, 10, 3],
            k=1,
        )[0]

    return colors[index]


def choose_grid(width, height):
    preferred = [
        20,
        24,
        25,
        30,
        32,
        40,
    ]

    valid = [
        size
        for size in preferred
        if width % size == 0
        and height % size == 0
    ]

    if valid:
        return random.choice(valid)

    return 20


# ============================================================
# 4. SVG BUILDING BLOCKS
# ============================================================

class ProductionSVG:

    def __init__(
        self,
        width,
        height,
        franchise,
    ):

        self.width = width
        self.height = height
        self.franchise = franchise

        self.defs = []
        self.objects = []

        self.object_counter = 0
        self.gradient_counter = 0

        self.config = CONFIG[franchise]
        self.prefix = self.config["prefix"]

    def next_object_id(self, kind):

        self.object_counter += 1

        return (
            f"{self.prefix}_"
            f"{kind}_"
            f"{self.object_counter:04d}"
        )

    def next_gradient_id(self):

        self.gradient_counter += 1

        return (
            f"{self.prefix}_gradient_"
            f"{self.gradient_counter:04d}"
        )

    # --------------------------------------------------------
    # GRADIENT
    # --------------------------------------------------------

    def create_gradient(
        self,
        bbox,
        pair=None,
        direction="horizontal",
        shimmer=False,
    ):

        if pair is None:
            pair = random.choice(
                self.config["gradients"]
            )

        x0, y0, x1, y1 = bbox

        gradient_id = self.next_gradient_id()

        if direction == "vertical":

            gx1 = x0
            gy1 = y0
            gx2 = x0
            gy2 = y1

        elif direction == "diagonal":

            gx1 = x0
            gy1 = y0
            gx2 = x1
            gy2 = y1

        else:

            gx1 = x0
            gy1 = y0
            gx2 = x1
            gy2 = y0

        if shimmer:

            middle = mix_colors(
                pair[0],
                "#FFFFFF",
                0.42,
            )

            stops = f"""
                <stop offset="0%" stop-color="{pair[0]}" />
                <stop offset="40%" stop-color="{pair[0]}" />
                <stop offset="51%" stop-color="{middle}" />
                <stop offset="61%" stop-color="{pair[1]}" />
                <stop offset="100%" stop-color="{pair[1]}" />
            """

        else:

            stops = f"""
                <stop offset="0%" stop-color="{pair[0]}" />
                <stop offset="100%" stop-color="{pair[1]}" />
            """

        definition = f"""
        <linearGradient
            id="{gradient_id}"
            gradientUnits="userSpaceOnUse"
            x1="{gx1}"
            y1="{gy1}"
            x2="{gx2}"
            y2="{gy2}">
            {stops}
        </linearGradient>
        """

        self.defs.append(definition)

        return f"url(#{gradient_id})"

    # --------------------------------------------------------
    # RECT
    # --------------------------------------------------------

    def rect(
        self,
        x,
        y,
        width,
        height,
        fill,
        kind="rect",
        rx=0,
    ):

        object_id = self.next_object_id(kind)

        self.objects.append(
            f"""
            <rect
                id="{object_id}"
                x="{x}"
                y="{y}"
                width="{width}"
                height="{height}"
                rx="{rx}"
                fill="{fill}"
            />
            """
        )

    # --------------------------------------------------------
    # CIRCLE
    # --------------------------------------------------------

    def circle(
        self,
        cx,
        cy,
        radius,
        fill,
        kind="circle",
    ):

        object_id = self.next_object_id(kind)

        self.objects.append(
            f"""
            <circle
                id="{object_id}"
                cx="{cx}"
                cy="{cy}"
                r="{radius}"
                fill="{fill}"
            />
            """
        )

    # --------------------------------------------------------
    # POLYGON
    # --------------------------------------------------------

    def polygon(
        self,
        points,
        fill,
        kind="polygon",
    ):

        object_id = self.next_object_id(kind)

        point_string = " ".join(
            f"{x},{y}"
            for x, y in points
        )

        self.objects.append(
            f"""
            <polygon
                id="{object_id}"
                points="{point_string}"
                fill="{fill}"
            />
            """
        )

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------

    def path(
        self,
        d,
        fill,
        kind="path",
    ):

        object_id = self.next_object_id(kind)

        self.objects.append(
            f"""
            <path
                id="{object_id}"
                d="{escape(d)}"
                fill="{fill}"
            />
            """
        )

    # --------------------------------------------------------
    # FINAL SVG
    # --------------------------------------------------------

    def render(self):

        return f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{self.width}"
    height="{self.height}"
    viewBox="0 0 {self.width} {self.height}">

    <title>{escape(self.franchise)} Production Vector</title>

    <desc>
        Animation-ready vector artwork.
        No masks.
        No clipping paths.
        No filters.
        No nested region hierarchy.
    </desc>

    <defs>
        {''.join(self.defs)}
    </defs>

    <rect
        id="BACKGROUND"
        x="0"
        y="0"
        width="{self.width}"
        height="{self.height}"
        fill="{PAPER}"
    />

    {''.join(self.objects)}

</svg>
"""


# ============================================================
# 5. REGION GENERATION
# ============================================================

def generate_regions(
    width,
    height,
    unit,
):

    macro = unit * random.choice(
        [4, 5, 6]
    )

    cols = math.ceil(width / macro)
    rows = math.ceil(height / macro)

    regions = []

    used = set()

    for row in range(rows):

        for col in range(cols):

            if (row, col) in used:
                continue

            span_x = random.choices(
                [1, 2, 3],
                weights=[50, 38, 12],
                k=1,
            )[0]

            span_y = random.choices(
                [1, 2, 3],
                weights=[50, 38, 12],
                k=1,
            )[0]

            cells = []

            valid = True

            for yy in range(
                row,
                min(rows, row + span_y),
            ):

                for xx in range(
                    col,
                    min(cols, col + span_x),
                ):

                    if (yy, xx) in used:
                        valid = False

                    cells.append(
                        (yy, xx)
                    )

            if not valid:

                cells = [
                    (row, col)
                ]

                span_x = 1
                span_y = 1

            for cell in cells:
                used.add(cell)

            x0 = col * macro
            y0 = row * macro

            x1 = min(
                width,
                x0 + span_x * macro,
            )

            y1 = min(
                height,
                y0 + span_y * macro,
            )

            regions.append(
                (x0, y0, x1, y1)
            )

    return regions


# ============================================================
# 6. FILL LOGIC
# ============================================================

def region_fill(
    svg,
    region,
    family,
    allow_gradient=True,
):

    if (
        allow_gradient
        and random.random() < 0.36
    ):

        direction = random.choice(
            [
                "horizontal",
                "horizontal",
                "vertical",
                "diagonal",
            ]
        )

        shimmer = (
            random.random() < 0.28
        )

        return svg.create_gradient(
            region,
            direction=direction,
            shimmer=shimmer,
        )

    return choose_family_color(
        svg.config,
        family,
    )


# ============================================================
# 7. MOTIF: CHECKER
# ============================================================

def draw_checker(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    cols = int(
        (x1 - x0) // unit
    )

    rows = int(
        (y1 - y0) // unit
    )

    color_a = choose_family_color(
        svg.config,
        family,
        "dark",
    )

    color_b = choose_family_color(
        svg.config,
        family,
        "light",
    )

    for row in range(rows):

        for col in range(cols):

            fill = (
                color_a
                if (row + col) % 2 == 0
                else color_b
            )

            svg.rect(
                x0 + col * unit,
                y0 + row * unit,
                unit,
                unit,
                fill,
                "checker",
            )


# ============================================================
# 8. MOTIF: DIAMONDS
# ============================================================

def draw_diamonds(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    cols = int(
        (x1 - x0) // unit
    )

    rows = int(
        (y1 - y0) // unit
    )

    colors = [
        choose_family_color(
            svg.config,
            family,
            "mid",
        ),
        choose_family_color(
            svg.config,
            family,
            "light",
        ),
    ]

    for row in range(rows):

        for col in range(cols):

            xx = x0 + col * unit
            yy = y0 + row * unit

            fill = colors[
                (row + col) % 2
            ]

            svg.polygon(
                [
                    (
                        xx + unit / 2,
                        yy,
                    ),
                    (
                        xx + unit,
                        yy + unit / 2,
                    ),
                    (
                        xx + unit / 2,
                        yy + unit,
                    ),
                    (
                        xx,
                        yy + unit / 2,
                    ),
                ],
                fill,
                "diamond",
            )


# ============================================================
# 9. MOTIF: CAPSULES
# ============================================================

def draw_capsules(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    horizontal = (
        random.random() < 0.5
    )

    if horizontal:

        rows = int(
            (y1 - y0) // unit
        )

        for row in range(rows):

            xx = x0

            while xx < x1:

                span = random.choice(
                    [2, 2, 3, 3, 4]
                )

                width = min(
                    span * unit,
                    x1 - xx,
                )

                bbox = (
                    xx,
                    y0 + row * unit,
                    xx + width,
                    y0 + (row + 1) * unit,
                )

                fill = region_fill(
                    svg,
                    bbox,
                    family,
                )

                svg.rect(
                    xx,
                    y0 + row * unit,
                    width,
                    unit,
                    fill,
                    "capsule",
                    rx=unit / 2,
                )

                xx += width

    else:

        cols = int(
            (x1 - x0) // unit
        )

        for col in range(cols):

            yy = y0

            while yy < y1:

                span = random.choice(
                    [2, 2, 3, 3, 4]
                )

                height = min(
                    span * unit,
                    y1 - yy,
                )

                bbox = (
                    x0 + col * unit,
                    yy,
                    x0 + (col + 1) * unit,
                    yy + height,
                )

                fill = region_fill(
                    svg,
                    bbox,
                    family,
                )

                svg.rect(
                    x0 + col * unit,
                    yy,
                    unit,
                    height,
                    fill,
                    "capsule",
                    rx=unit / 2,
                )

                yy += height


# ============================================================
# 10. MOTIF: LATTICE
# ============================================================

def draw_lattice(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    cols = int(
        (x1 - x0) // unit
    )

    rows = int(
        (y1 - y0) // unit
    )

    fill = choose_family_color(
        svg.config,
        family,
        "mid",
    )

    for row in range(rows):

        for col in range(cols):

            if (
                row % 2 == 0
                or col % 2 == 0
            ):

                svg.circle(
                    x0 + col * unit + unit / 2,
                    y0 + row * unit + unit / 2,
                    unit / 2,
                    fill,
                    "lattice_circle",
                )


# ============================================================
# 11. MOTIF: CELLULAR
# ============================================================

def draw_cellular(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    cols = int(
        (x1 - x0) // unit
    )

    rows = int(
        (y1 - y0) // unit
    )

    fill = choose_family_color(
        svg.config,
        family,
        "mid",
    )

    for row in range(
        0,
        rows,
        3,
    ):

        for col in range(
            0,
            cols,
            3,
        ):

            points = [
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
                (row + 1, col + 2),
                (row + 2, col + 1),
            ]

            for rr, cc in points:

                if (
                    rr < rows
                    and cc < cols
                ):

                    svg.circle(
                        x0 + cc * unit + unit / 2,
                        y0 + rr * unit + unit / 2,
                        unit / 2,
                        fill,
                        "cellular_circle",
                    )


# ============================================================
# 12. MOTIF: VERTEBRA
# ============================================================

def draw_vertebra(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    width = x1 - x0
    height = y1 - y0

    cols = max(
        3,
        int(width // unit),
    )

    rows = max(
        3,
        int(height // unit),
    )

    spine = cols // 2

    fill = region_fill(
        svg,
        region,
        family,
    )

    # Build one compound architectural path.

    segments = []

    for row in range(rows):

        y = y0 + row * unit

        center_x = (
            x0 + spine * unit
        )

        segments.append(
            f"M {center_x} {y} "
            f"H {center_x + unit} "
            f"V {y + unit} "
            f"H {center_x} Z"
        )

        if row % 2 == 0:

            reach = min(
                2,
                spine,
                cols - spine - 1,
            )

            left_x = (
                center_x
                - reach * unit
            )

            right_x = (
                center_x
                +
                (reach + 1) * unit
            )

            segments.append(
                f"M {left_x} {y} "
                f"H {right_x} "
                f"V {y + unit} "
                f"H {left_x} Z"
            )

    svg.path(
        " ".join(segments),
        fill,
        "vertebra",
    )


# ============================================================
# 13. MOTIF: SCAFFOLD
# ============================================================

def draw_scaffold(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    fill = region_fill(
        svg,
        region,
        family,
        allow_gradient=False,
    )

    width = x1 - x0
    height = y1 - y0

    thickness = unit

    path_parts = []

    # vertical posts
    x = x0

    while x < x1:

        path_parts.append(
            f"M {x} {y0} "
            f"H {min(x + thickness, x1)} "
            f"V {y1} "
            f"H {x} Z"
        )

        x += unit * 3

    # horizontal bars
    y = y0 + unit

    while y < y1:

        path_parts.append(
            f"M {x0} {y} "
            f"H {x1} "
            f"V {min(y + thickness, y1)} "
            f"H {x0} Z"
        )

        y += unit * 3

    svg.path(
        " ".join(path_parts),
        fill,
        "scaffold",
    )


# ============================================================
# 14. MOTIF: STAIRS
# ============================================================

def draw_stairs(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    cols = max(
        1,
        int(
            (x1 - x0) // unit
        ),
    )

    rows = max(
        1,
        int(
            (y1 - y0) // unit
        ),
    )

    count = min(
        cols,
        rows,
    )

    fill = region_fill(
        svg,
        region,
        family,
    )

    mirror = random.random() < 0.5

    path_parts = []

    for index in range(count):

        if mirror:
            col = (
                cols - 1 - index
            )
        else:
            col = index

        row = index

        xx = x0 + col * unit
        yy = y0 + row * unit

        path_parts.append(
            f"M {xx} {yy} "
            f"H {xx + unit} "
            f"V {yy + unit} "
            f"H {xx} Z"
        )

    svg.path(
        " ".join(path_parts),
        fill,
        "stairs",
    )


# ============================================================
# 15. MOTIF: SAW BLOCK
# ============================================================

def draw_saw_block(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    fill = region_fill(
        svg,
        region,
        family,
    )

    teeth = max(
        2,
        int(
            (x1 - x0)
            // unit
        ),
    )

    points = [
        (x0, y1),
        (x0, y0 + unit),
    ]

    x = x0

    for _ in range(teeth):

        points.append(
            (x, y0 + unit)
        )

        points.append(
            (
                x + unit / 2,
                y0,
            )
        )

        points.append(
            (
                min(x + unit, x1),
                y0 + unit,
            )
        )

        x += unit

        if x >= x1:
            break

    points.extend(
        [
            (x1, y1),
            (x0, y1),
        ]
    )

    svg.polygon(
        points,
        fill,
        "saw_block",
    )


# ============================================================
# 16. MOTIF: ARCHITECTURAL BLOCK
# ============================================================

def draw_architectural(
    svg,
    region,
    unit,
    family,
):

    x0, y0, x1, y1 = region

    fill = region_fill(
        svg,
        region,
        family,
    )

    cols = max(
        1,
        int(
            (x1 - x0) // unit
        ),
    )

    rows = max(
        1,
        int(
            (y1 - y0) // unit
        ),
    )

    path_parts = []

    for row in range(rows):

        # Mostly solid mass,
        # with occasional full-grid-cell openings.

        for col in range(cols):

            if (
                random.random() < 0.08
            ):
                continue

            xx = x0 + col * unit
            yy = y0 + row * unit

            path_parts.append(
                f"M {xx} {yy} "
                f"H {xx + unit} "
                f"V {yy + unit} "
                f"H {xx} Z"
            )

    svg.path(
        " ".join(path_parts),
        fill,
        "architectural_block",
    )


# ============================================================
# 17. CLEAN GEOMETRIC SPLICE
# ============================================================

def draw_spliced_rect(
    svg,
    region,
    family_a,
    family_b,
):

    x0, y0, x1, y1 = region

    color_a = choose_family_color(
        svg.config,
        family_a,
        "mid",
    )

    color_b = choose_family_color(
        svg.config,
        family_b,
        "mid",
    )

    # True geometric diagonal split.
    # No clipping mask.

    svg.polygon(
        [
            (x0, y0),
            (x1, y0),
            (x0, y1),
        ],
        color_a,
        "splice_base",
    )

    svg.polygon(
        [
            (x1, y0),
            (x1, y1),
            (x0, y1),
        ],
        color_b,
        "splice_accent",
    )


# ============================================================
# 18. MOTIF DISPATCH
# ============================================================

def draw_motif(
    svg,
    motif,
    region,
    unit,
    family,
):

    if motif == "checker":

        draw_checker(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "diamonds":

        draw_diamonds(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "capsules":

        draw_capsules(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "lattice":

        draw_lattice(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "cellular":

        draw_cellular(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "vertebra":

        draw_vertebra(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "scaffold":

        draw_scaffold(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "stairs":

        draw_stairs(
            svg,
            region,
            unit,
            family,
        )

    elif motif == "saw_block":

        draw_saw_block(
            svg,
            region,
            unit,
            family,
        )

    else:

        draw_architectural(
            svg,
            region,
            unit,
            family,
        )


# ============================================================
# 19. MAIN PRODUCTION VECTOR GENERATOR
# ============================================================

def generate_production_vector(
    franchise,
    width,
    height,
    seed=None,
):

    if franchise not in CONFIG:
        raise ValueError(
            f"Unknown franchise: {franchise}"
        )

    if seed is None:

        seed = random.randint(
            0,
            999_999_999,
        )

    random.seed(seed)

    width = int(width)
    height = int(height)

    unit = choose_grid(
        width,
        height,
    )

    svg = ProductionSVG(
        width,
        height,
        franchise,
    )

    config = CONFIG[franchise]

    regions = generate_regions(
        width,
        height,
        unit,
    )

    previous_motif = None
    previous_family = None

    splice_count = 0

    for region in regions:

        # ----------------------------------------------------
        # REPEAT MOTIFS ENOUGH TO FEEL LIKE A PATTERN
        # ----------------------------------------------------

        if (
            previous_motif
            and random.random() < 0.32
        ):

            motif = previous_motif

        else:

            motif = random.choice(
                config["motifs"]
            )

        # ----------------------------------------------------
        # REPEAT COLOR ENOUGH TO CREATE FAMILY / FIELD
        # ----------------------------------------------------

        if (
            previous_family
            and random.random() < 0.28
        ):

            family = previous_family

        else:

            family = choose_family(
                config
            )

        # ----------------------------------------------------
        # OCCASIONAL CLEAN SPLICE EVENT
        # ----------------------------------------------------

        can_splice = (
            motif
            in [
                "architectural",
                "saw_block",
                "stairs",
            ]
        )

        if (
            can_splice
            and random.random() < 0.20
        ):

            other_families = [
                item
                for item
                in config["palette"]
                if item != family
            ]

            other_family = random.choice(
                other_families
            )

            draw_spliced_rect(
                svg,
                region,
                family,
                other_family,
            )

            splice_count += 1

        else:

            draw_motif(
                svg,
                motif,
                region,
                unit,
                family,
            )

        previous_motif = motif
        previous_family = family

    output = svg.render()

    metadata = {
        "seed": seed,
        "franchise": franchise,
        "width": width,
        "height": height,
        "grid": unit,
        "objects": svg.object_counter,
        "gradients": svg.gradient_counter,
        "splices": splice_count,
    }

    return (
        output,
        metadata,
    )


# ============================================================
# 20. CONVENIENCE FUNCTIONS
# ============================================================

def generate_ai_edge_production_vector(
    width,
    height,
    seed=None,
):

    return generate_production_vector(
        "AI Edge",
        width,
        height,
        seed,
    )


def generate_vital_edge_production_vector(
    width,
    height,
    seed=None,
):

    return generate_production_vector(
        "Vital Edge",
        width,
        height,
        seed,
    )


# ============================================================
# 21. LOCAL TEST
# ============================================================

if __name__ == "__main__":

    svg_string, info = (
        generate_ai_edge_production_vector(
            1200,
            1600,
        )
    )

    filename = (
        "ai_edge_production_vector.svg"
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            svg_string
        )

    print()
    print(
        "PRODUCTION VECTOR GENERATED"
    )
    print(
        f"File: {filename}"
    )
    print(
        f"Objects: {info['objects']}"
    )
    print(
        f"Gradients: {info['gradients']}"
    )
    print(
        f"Splices: {info['splices']}"
    )