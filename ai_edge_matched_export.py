import math
import random

from PIL import Image

from shapely.geometry import (
    Point,
    Polygon,
    box,
)
from shapely.geometry.base import BaseGeometry

import ai_edge_generator as ai


# ============================================================
# AI EDGE MATCHED PRODUCTION EXPORT
# ============================================================
#
# IMPORTANT:
#
# This file DOES NOT recreate the AI Edge composition.
#
# Instead it runs the approved ai_edge_generator.py twice
# using the exact same seed:
#
#   PASS 1
#       Approved Pillow renderer -> PNG
#
#   PASS 2
#       Same generator logic
#       Same random decisions
#       Same macro regions
#       Same motifs
#       Same colors
#       Same gradients
#       Same splice
#
#       But render_shape() is temporarily replaced by a
#       recorder which stores final vector instructions.
#
# Those instructions are then converted into a clean SVG:
#
#   - no clipping paths
#   - no SVG masks
#   - no nested region groups
#   - no raster grain
#   - no SVG filters
#   - true editable gradients
#   - repeated primitives remain individual objects
#   - spliced shapes become actual intersected paths
#
# ============================================================


PAPER = ai.PAPER


# ============================================================
# BASIC HELPERS
# ============================================================

def clamp(value, minimum, maximum):

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def rgb_to_hex(rgb):

    return "#{:02X}{:02X}{:02X}".format(
        int(
            clamp(
                round(rgb[0]),
                0,
                255,
            )
        ),
        int(
            clamp(
                round(rgb[1]),
                0,
                255,
            )
        ),
        int(
            clamp(
                round(rgb[2]),
                0,
                255,
            )
        ),
    )


def seed_generator(seed):

    ai.SEED = seed

    ai.random.seed(
        seed
    )

    ai.np.random.seed(
        seed
    )


# ============================================================
# SHAPE -> CLEAN VECTOR GEOMETRY
# ============================================================

def shape_geometry(
    bbox,
    shape,
):

    x0, y0, x1, y1 = bbox

    width = x1 - x0
    height = y1 - y0

    if width <= 0 or height <= 0:

        return Polygon()

    # --------------------------------------------------------
    # RECT
    # --------------------------------------------------------

    if shape == "rect":

        return box(
            x0,
            y0,
            x1,
            y1,
        )

    # --------------------------------------------------------
    # CIRCLE
    #
    # Matches the Pillow implementation:
    # circle uses min(width, height), centered in bbox.
    # --------------------------------------------------------

    if shape == "circle":

        size = min(
            width,
            height,
        )

        radius = size / 2

        cx = (
            x0 + x1
        ) / 2

        cy = (
            y0 + y1
        ) / 2

        return Point(
            cx,
            cy,
        ).buffer(
            radius,
            resolution=16,
        )

    # --------------------------------------------------------
    # DIAMOND
    # --------------------------------------------------------

    if shape == "diamond":

        cx = (
            x0 + x1
        ) / 2

        cy = (
            y0 + y1
        ) / 2

        return Polygon(
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
            ]
        )

    # --------------------------------------------------------
    # TRIANGLE UP
    # --------------------------------------------------------

    if shape == "triangle_up":

        return Polygon(
            [
                (
                    (
                        x0 + x1
                    ) / 2,
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
            ]
        )

    # --------------------------------------------------------
    # TRIANGLE DOWN
    # --------------------------------------------------------

    if shape == "triangle_down":

        return Polygon(
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
                    (
                        x0 + x1
                    ) / 2,
                    y1,
                ),
            ]
        )

    # --------------------------------------------------------
    # CAPSULE
    # --------------------------------------------------------

    if shape == "capsule":

        radius = min(
            width,
            height,
        ) / 2

        # horizontal capsule

        if width >= height:

            cy = (
                y0 + y1
            ) / 2

            left_x = (
                x0 + radius
            )

            right_x = (
                x1 - radius
            )

            center = box(
                left_x,
                y0,
                right_x,
                y1,
            )

            left = Point(
                left_x,
                cy,
            ).buffer(
                radius,
                resolution=16,
            )

            right = Point(
                right_x,
                cy,
            ).buffer(
                radius,
                resolution=16,
            )

            return (
                center
                .union(left)
                .union(right)
            )

        # vertical capsule

        cx = (
            x0 + x1
        ) / 2

        top_y = (
            y0 + radius
        )

        bottom_y = (
            y1 - radius
        )

        center = box(
            x0,
            top_y,
            x1,
            bottom_y,
        )

        top = Point(
            cx,
            top_y,
        ).buffer(
            radius,
            resolution=16,
        )

        bottom = Point(
            cx,
            bottom_y,
        ).buffer(
            radius,
            resolution=16,
        )

        return (
            center
            .union(top)
            .union(bottom)
        )

    return box(
        x0,
        y0,
        x1,
        y1,
    )


# ============================================================
# SHAPELY GEOMETRY -> SVG PATH
# ============================================================

def ring_to_path(coords):

    coords = list(coords)

    if not coords:

        return ""

    parts = [
        f"M {coords[0][0]:.3f} {coords[0][1]:.3f}"
    ]

    for x, y in coords[1:]:

        parts.append(
            f"L {x:.3f} {y:.3f}"
        )

    parts.append(
        "Z"
    )

    return " ".join(
        parts
    )


def polygon_to_path(
    polygon,
):

    if polygon.is_empty:

        return ""

    result = [
        ring_to_path(
            polygon.exterior.coords
        )
    ]

    for interior in polygon.interiors:

        result.append(
            ring_to_path(
                interior.coords
            )
        )

    return " ".join(
        result
    )


def geometry_to_path(
    geometry,
):

    if geometry is None:

        return ""

    if geometry.is_empty:

        return ""

    geom_type = geometry.geom_type

    if geom_type == "Polygon":

        return polygon_to_path(
            geometry
        )

    if geom_type == "MultiPolygon":

        return " ".join(
            polygon_to_path(
                polygon
            )
            for polygon
            in geometry.geoms
            if not polygon.is_empty
        )

    if geom_type == "GeometryCollection":

        return " ".join(
            geometry_to_path(
                item
            )
            for item
            in geometry.geoms
            if not item.is_empty
        )

    return ""


# ============================================================
# GLOBAL SPLICE GEOMETRY
# ============================================================

def create_splice_polygon(
    width,
    height,
    small_unit,
    direction,
    position,
):

    span = (
        width
        +
        height
    )

    # --------------------------------------------------------
    # SAME MATH AS ai_edge_generator.create_splice_mask()
    # --------------------------------------------------------

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

        points = [
            (
                0,
                b,
            ),
            (
                width,
                width + b,
            ),
            (
                width,
                height
                +
                width
                +
                small_unit,
            ),
            (
                0,
                height
                +
                small_unit,
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

        points = [
            (
                0,
                -height
                -
                small_unit,
            ),
            (
                width,
                -height
                -
                small_unit,
            ),
            (
                width,
                b - width,
            ),
            (
                0,
                b,
            ),
        ]

    return Polygon(
        points
    )


# ============================================================
# SVG GRADIENT HELPERS
# ============================================================

def smoothstep(t):

    return (
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


def gradient_rgb_at(
    pair,
    t,
    shimmer,
    shimmer_phase,
):

    t = clamp(
        t,
        0.0,
        1.0,
    )

    eased = smoothstep(
        t
    )

    rgb = list(
        ai.sample_gradient(
            pair,
            eased,
        )
    )

    # --------------------------------------------------------
    # SAME GENERAL SHIMMER FIELD AS TRUE GRADIENT PATCH
    #
    # SVG cannot store the pixel-level NumPy raster field,
    # so it is represented as additional gradient stops.
    #
    # It remains one live gradient rather than a masked
    # duplicate object.
    # --------------------------------------------------------

    if shimmer:

        shimmer_value = (
            math.sin(
                (
                    eased
                    *
                    math.pi
                    *
                    2.25
                )
                +
                shimmer_phase
            )
            *
            7.0
        )

        shimmer_value += (
            math.sin(
                (
                    eased
                    *
                    math.pi
                    *
                    4.5
                )
                -
                shimmer_phase
                *
                0.6
            )
            *
            2.5
        )

        rgb = [
            clamp(
                channel
                +
                shimmer_value,
                0,
                255,
            )
            for channel
            in rgb
        ]

    return tuple(
        rgb
    )


# ============================================================
# PRODUCTION VECTOR RECORDER
# ============================================================

class ProductionRecorder:

    def __init__(
        self,
        width,
        height,
    ):

        self.width = width
        self.height = height

        self.commands = []

        self.current_motif = "shape"

        self.splice_direction = None
        self.splice_position = None
        self.splice_small_unit = None

        self.counter = 0

    def set_motif(
        self,
        motif,
    ):

        self.current_motif = motif

    def capture_splice(
        self,
        small_unit,
        direction,
        position,
    ):

        self.splice_small_unit = (
            small_unit
        )

        self.splice_direction = (
            direction
        )

        self.splice_position = (
            position
        )

    def record_shape(
        self,
        bbox,
        shape,
        row,
        col,
        rows,
        cols,
        settings,
        region,
    ):

        # ----------------------------------------------------
        # IMPORTANT RANDOM-SEQUENCE PRESERVATION
        #
        # The approved render_shape() consumes exactly one
        # random.randint(224, 244) for each primitive.
        #
        # We consume the same draw here so later motif choices
        # remain identical to the PNG run.
        # ----------------------------------------------------

        alpha = ai.random.randint(
            224,
            244,
        )

        if settings["gradient"]:

            spot_color = None

        else:

            spot_color = (
                ai.region_spot_color(
                    row,
                    col,
                    rows,
                    cols,
                    settings,
                )
            )

        self.counter += 1

        self.commands.append(
            {
                "id":
                    self.counter,

                "motif":
                    self.current_motif,

                "bbox":
                    tuple(
                        float(v)
                        for v
                        in bbox
                    ),

                "shape":
                    shape,

                "row":
                    row,

                "col":
                    col,

                "rows":
                    rows,

                "cols":
                    cols,

                "region":
                    tuple(
                        float(v)
                        for v
                        in region
                    ),

                "family":
                    settings["family"],

                "gradient":
                    bool(
                        settings["gradient"]
                    ),

                "gradient_pair":
                    tuple(
                        settings[
                            "gradient_pair"
                        ]
                    ),

                "gradient_axis":
                    settings[
                        "gradient_axis"
                    ],

                "shimmer":
                    bool(
                        settings["shimmer"]
                    ),

                "shimmer_phase":
                    float(
                        settings[
                            "shimmer_phase"
                        ]
                    ),

                "splice":
                    bool(
                        settings["splice"]
                    ),

                "splice_color":
                    tuple(
                        settings[
                            "splice_color"
                        ]
                    ),

                "spot_color":
                    spot_color,

                "alpha":
                    alpha,
            }
        )


# ============================================================
# SVG WRITER
# ============================================================

class ProductionSVG:

    def __init__(
        self,
        width,
        height,
        recorder,
    ):

        self.width = width
        self.height = height
        self.recorder = recorder

        self.defs = []

        self.objects = []

        self.gradient_ids = {}

        self.gradient_counter = 0

    # --------------------------------------------------------
    # GRADIENT DEFINITION
    # --------------------------------------------------------

    def gradient_id_for(
        self,
        command,
    ):

        region = command[
            "region"
        ]

        key = (
            region,
            command[
                "gradient_pair"
            ],
            command[
                "gradient_axis"
            ],
            command[
                "shimmer"
            ],
            round(
                command[
                    "shimmer_phase"
                ],
                5,
            ),
        )

        if key in self.gradient_ids:

            return self.gradient_ids[
                key
            ]

        self.gradient_counter += 1

        gradient_id = (
            f"AI_gradient_"
            f"{self.gradient_counter:04d}"
        )

        self.gradient_ids[
            key
        ] = gradient_id

        x0, y0, x1, y1 = region

        axis = command[
            "gradient_axis"
        ]

        if axis == "x":

            gx1 = x0
            gy1 = y0
            gx2 = x1
            gy2 = y0

        elif axis == "y":

            gx1 = x0
            gy1 = y0
            gx2 = x0
            gy2 = y1

        elif axis == "diag_down":

            gx1 = x0
            gy1 = y0
            gx2 = x1
            gy2 = y1

        else:

            gx1 = x0
            gy1 = y1
            gx2 = x1
            gy2 = y0

        stops = []

        # ----------------------------------------------------
        # Several stops reproduce the eased Pillow gradient
        # while remaining a single live Illustrator gradient.
        # ----------------------------------------------------

        stop_count = 13

        for index in range(
            stop_count
        ):

            t = (
                index
                /
                (
                    stop_count
                    -
                    1
                )
            )

            rgb = gradient_rgb_at(
                command[
                    "gradient_pair"
                ],
                t,
                command[
                    "shimmer"
                ],
                command[
                    "shimmer_phase"
                ],
            )

            stops.append(
                (
                    t,
                    rgb_to_hex(
                        rgb
                    ),
                )
            )

        stop_markup = "\n".join(
            (
                f'<stop '
                f'offset="{t * 100:.3f}%" '
                f'stop-color="{color}" />'
            )
            for t, color
            in stops
        )

        self.defs.append(
            f"""
<linearGradient
    id="{gradient_id}"
    gradientUnits="userSpaceOnUse"
    x1="{gx1:.3f}"
    y1="{gy1:.3f}"
    x2="{gx2:.3f}"
    y2="{gy2:.3f}">
{stop_markup}
</linearGradient>
"""
        )

        return gradient_id

    # --------------------------------------------------------
    # SHAPE ID
    # --------------------------------------------------------

    def shape_id(
        self,
        command,
        suffix=None,
    ):

        motif = (
            command["motif"]
            .replace(
                " ",
                "_",
            )
        )

        shape = (
            command["shape"]
            .replace(
                " ",
                "_",
            )
        )

        base = (
            f"AI_"
            f"{motif}_"
            f"{shape}_"
            f"{command['id']:04d}"
        )

        if suffix:

            return (
                f"{base}_"
                f"{suffix}"
            )

        return base

    # --------------------------------------------------------
    # UNSPLICED NATIVE ELEMENT
    # --------------------------------------------------------

    def native_shape_markup(
        self,
        command,
        fill,
        opacity,
    ):

        x0, y0, x1, y1 = (
            command["bbox"]
        )

        width = x1 - x0
        height = y1 - y0

        shape = command[
            "shape"
        ]

        object_id = self.shape_id(
            command
        )

        # ----------------------------------------------------
        # RECT
        # ----------------------------------------------------

        if shape == "rect":

            return f"""
<rect
    id="{object_id}"
    x="{x0:.3f}"
    y="{y0:.3f}"
    width="{width:.3f}"
    height="{height:.3f}"
    fill="{fill}"
    fill-opacity="{opacity:.4f}"
/>
"""

        # ----------------------------------------------------
        # CIRCLE
        # ----------------------------------------------------

        if shape == "circle":

            size = min(
                width,
                height,
            )

            radius = (
                size / 2
            )

            cx = (
                x0 + x1
            ) / 2

            cy = (
                y0 + y1
            ) / 2

            return f"""
<circle
    id="{object_id}"
    cx="{cx:.3f}"
    cy="{cy:.3f}"
    r="{radius:.3f}"
    fill="{fill}"
    fill-opacity="{opacity:.4f}"
/>
"""

        # ----------------------------------------------------
        # CAPSULE
        # ----------------------------------------------------

        if shape == "capsule":

            radius = min(
                width,
                height,
            ) / 2

            return f"""
<rect
    id="{object_id}"
    x="{x0:.3f}"
    y="{y0:.3f}"
    width="{width:.3f}"
    height="{height:.3f}"
    rx="{radius:.3f}"
    ry="{radius:.3f}"
    fill="{fill}"
    fill-opacity="{opacity:.4f}"
/>
"""

        # ----------------------------------------------------
        # POLYGON PRIMITIVES
        # ----------------------------------------------------

        geometry = shape_geometry(
            command[
                "bbox"
            ],
            shape,
        )

        path = geometry_to_path(
            geometry
        )

        return f"""
<path
    id="{object_id}"
    d="{path}"
    fill="{fill}"
    fill-opacity="{opacity:.4f}"
    fill-rule="evenodd"
/>
"""

    # --------------------------------------------------------
    # SPLIT OBJECT
    # --------------------------------------------------------

    def spliced_shape_markup(
        self,
        command,
        primary_fill,
        primary_opacity,
        splice_polygon,
    ):

        geometry = shape_geometry(
            command[
                "bbox"
            ],
            command[
                "shape"
            ],
        )

        if geometry.is_empty:

            return ""

        side_a = geometry.intersection(
            splice_polygon
        )

        side_b = geometry.difference(
            splice_polygon
        )

        result = []

        if not side_a.is_empty:

            path_a = geometry_to_path(
                side_a
            )

            if path_a:

                result.append(
                    f"""
<path
    id="{self.shape_id(command, 'A')}"
    d="{path_a}"
    fill="{primary_fill}"
    fill-opacity="{primary_opacity:.4f}"
    fill-rule="evenodd"
/>
"""
                )

        if not side_b.is_empty:

            path_b = geometry_to_path(
                side_b
            )

            if path_b:

                splice_color = rgb_to_hex(
                    command[
                        "splice_color"
                    ]
                )

                splice_opacity = (
                    command[
                        "alpha"
                    ]
                    /
                    255.0
                )

                result.append(
                    f"""
<path
    id="{self.shape_id(command, 'B')}"
    d="{path_b}"
    fill="{splice_color}"
    fill-opacity="{splice_opacity:.4f}"
    fill-rule="evenodd"
/>
"""
                )

        return "\n".join(
            result
        )

    # --------------------------------------------------------
    # BUILD ARTWORK
    # --------------------------------------------------------

    def build(
        self,
    ):

        splice_polygon = None

        if (
            self.recorder.splice_direction
            is not None
        ):

            splice_polygon = (
                create_splice_polygon(
                    self.width,
                    self.height,
                    self.recorder
                    .splice_small_unit,
                    self.recorder
                    .splice_direction,
                    self.recorder
                    .splice_position,
                )
            )

        for command in (
            self.recorder.commands
        ):

            # ------------------------------------------------
            # PRIMARY FILL
            # ------------------------------------------------

            if command["gradient"]:

                gradient_id = (
                    self.gradient_id_for(
                        command
                    )
                )

                primary_fill = (
                    f"url(#{gradient_id})"
                )

                # True gradient patch in approved generator
                # uses alpha 238.

                primary_opacity = (
                    238
                    /
                    255.0
                )

            else:

                primary_fill = rgb_to_hex(
                    command[
                        "spot_color"
                    ]
                )

                primary_opacity = (
                    command[
                        "alpha"
                    ]
                    /
                    255.0
                )

            # ------------------------------------------------
            # SPLICE
            # ------------------------------------------------

            if (
                command["splice"]
                and
                splice_polygon
                is not None
            ):

                markup = (
                    self.spliced_shape_markup(
                        command,
                        primary_fill,
                        primary_opacity,
                        splice_polygon,
                    )
                )

            else:

                markup = (
                    self.native_shape_markup(
                        command,
                        primary_fill,
                        primary_opacity,
                    )
                )

            self.objects.append(
                markup
            )

    # --------------------------------------------------------
    # FINAL SVG
    # --------------------------------------------------------

    def render(
        self,
    ):

        self.build()

        defs = "\n".join(
            self.defs
        )

        objects = "\n".join(
            self.objects
        )

        return f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{self.width}"
    height="{self.height}"
    viewBox="0 0 {self.width} {self.height}">

<title>
AI Edge Production Vector
</title>

<desc>
Generated from the exact same AI Edge composition
logic and random seed as the PNG preview.

No clipping masks.
No SVG masks.
No raster grain.
No nested region hierarchy.
Individual pattern primitives remain editable.
</desc>

<defs>
{defs}
</defs>

<rect
    id="BACKGROUND"
    x="0"
    y="0"
    width="{self.width}"
    height="{self.height}"
    fill="{PAPER}"
/>

{objects}

</svg>
"""


# ============================================================
# VECTOR RECORDING PASS
# ============================================================

def record_vector_composition(
    width,
    height,
    seed,
):

    recorder = ProductionRecorder(
        width,
        height,
    )

    # --------------------------------------------------------
    # SAVE ORIGINAL GENERATOR FUNCTIONS
    # --------------------------------------------------------

    original_render_shape = (
        ai.render_shape
    )

    original_render_motif = (
        ai.render_motif
    )

    original_create_splice_mask = (
        ai.create_splice_mask
    )

    original_make_paper = (
        ai.make_paper
    )

    original_apply_print_texture = (
        ai.apply_print_texture
    )

    original_add_overprint = (
        ai.add_overprint
    )

    # --------------------------------------------------------
    # FAST BLANK PAPER
    #
    # We do NOT need to render the second raster copy.
    # Composition randomness comes from Python's random module.
    # --------------------------------------------------------

    def recording_make_paper(
        w,
        h,
    ):

        return Image.new(
            "RGB",
            (
                ai.hi(w),
                ai.hi(h),
            ),
            ai.hex_to_rgb(
                ai.PAPER
            ),
        )

    # --------------------------------------------------------
    # NO PRINT TEXTURE DURING RECORDING PASS
    # --------------------------------------------------------

    def recording_apply_print_texture(
        image,
    ):

        return image

    # --------------------------------------------------------
    # OVERPRINT IS INTENTIONALLY OMITTED FROM PRODUCTION VECTOR
    #
    # It happens after motif construction, so skipping it does
    # not alter previously recorded composition decisions.
    # --------------------------------------------------------

    def recording_add_overprint(
        canvas,
        w,
        h,
        small_unit,
    ):

        return

    # --------------------------------------------------------
    # CAPTURE GLOBAL SPLICE SETTINGS
    # --------------------------------------------------------

    def recording_create_splice_mask(
        w,
        h,
        small_unit,
        direction,
        position,
    ):

        recorder.capture_splice(
            small_unit,
            direction,
            position,
        )

        return (
            original_create_splice_mask(
                w,
                h,
                small_unit,
                direction,
                position,
            )
        )

    # --------------------------------------------------------
    # CAPTURE CURRENT MOTIF NAME
    # --------------------------------------------------------

    def recording_render_motif(
        canvas,
        region,
        motif,
        small_unit,
        settings,
        splice_mask,
    ):

        recorder.set_motif(
            motif
        )

        return original_render_motif(
            canvas,
            region,
            motif,
            small_unit,
            settings,
            splice_mask,
        )

    # --------------------------------------------------------
    # REPLACE FINAL PRIMITIVE DRAW CALL
    # --------------------------------------------------------

    def recording_render_shape(
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

        recorder.record_shape(
            bbox,
            shape,
            row,
            col,
            rows,
            cols,
            settings,
            region,
        )

    # --------------------------------------------------------
    # INSTALL TEMPORARY RECORDING FUNCTIONS
    # --------------------------------------------------------

    ai.render_shape = (
        recording_render_shape
    )

    ai.render_motif = (
        recording_render_motif
    )

    ai.create_splice_mask = (
        recording_create_splice_mask
    )

    ai.make_paper = (
        recording_make_paper
    )

    ai.apply_print_texture = (
        recording_apply_print_texture
    )

    ai.add_overprint = (
        recording_add_overprint
    )

    try:

        seed_generator(
            seed
        )

        # Run the APPROVED generator.
        #
        # Motif functions remain untouched.
        # Region construction remains untouched.
        # All random motif decisions remain untouched.

        ai.generate_ai_edge_pattern(
            width,
            height,
        )

    finally:

        # ----------------------------------------------------
        # ALWAYS RESTORE ORIGINAL GENERATOR
        # ----------------------------------------------------

        ai.render_shape = (
            original_render_shape
        )

        ai.render_motif = (
            original_render_motif
        )

        ai.create_splice_mask = (
            original_create_splice_mask
        )

        ai.make_paper = (
            original_make_paper
        )

        ai.apply_print_texture = (
            original_apply_print_texture
        )

        ai.add_overprint = (
            original_add_overprint
        )

    return recorder


# ============================================================
# MAIN MATCHED GENERATOR
# ============================================================

def generate_ai_edge_matched(
    width,
    height,
    seed=None,
):

    width = int(
        width
    )

    height = int(
        height
    )

    if seed is None:

        seed = (
            random.SystemRandom()
            .randint(
                0,
                999_999_999,
            )
        )

    # ========================================================
    # PASS 1 — APPROVED PNG
    # ========================================================

    seed_generator(
        seed
    )

    image, metadata = (
        ai.generate_ai_edge_pattern(
            width,
            height,
        )
    )

    metadata = dict(
        metadata
    )

    metadata[
        "seed"
    ] = seed

    # ========================================================
    # PASS 2 — SAME COMPOSITION -> VECTOR RECORD
    # ========================================================

    recorder = (
        record_vector_composition(
            width,
            height,
            seed,
        )
    )

    svg_builder = ProductionSVG(
        width,
        height,
        recorder,
    )

    production_vector = (
        svg_builder.render()
    )

    vector_metadata = {
        "seed":
            seed,

        "object_count":
            len(
                recorder.commands
            ),

        "gradient_count":
            svg_builder
            .gradient_counter,

        "splice_direction":
            recorder
            .splice_direction,

        "splice_position":
            recorder
            .splice_position,

        "small_unit":
            recorder
            .splice_small_unit,
    }

    return (
        image,
        metadata,
        production_vector,
        vector_metadata,
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    WIDTH = 1200
    HEIGHT = 1600

    (
        image,
        png_info,
        production_vector,
        vector_info,
    ) = generate_ai_edge_matched(
        WIDTH,
        HEIGHT,
    )

    seed = png_info[
        "seed"
    ]

    png_filename = (
        f"ai_edge_matched_"
        f"{seed}.png"
    )

    svg_filename = (
        f"ai_edge_matched_"
        f"{seed}.svg"
    )

    image.save(
        png_filename
    )

    with open(
        svg_filename,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            production_vector
        )

    print()

    print(
        "========================================"
    )

    print(
        " AI EDGE MATCHED EXPORT GENERATED"
    )

    print(
        "========================================"
    )

    print(
        f" Seed:          {seed}"
    )

    print(
        f" PNG:           {png_filename}"
    )

    print(
        f" Vector:        {svg_filename}"
    )

    print(
        f" Vector objects:"
        f" {vector_info['object_count']}"
    )

    print(
        f" Gradients:     "
        f"{vector_info['gradient_count']}"
    )

    print(
        "========================================"
    )