# ============================================================
# AI EDGE PRODUCTION VECTOR
# ai_edge_vector.py
# ============================================================
#
# Converts the SAME CompositionBlueprint used by the PNG
# renderer into clean editable SVG.
#
# Rules:
#
# - exact visual composition from blueprint
# - one editable SVG object per primitive
# - flat spot colors only
# - no gradients
# - no shimmer
# - no opacity variation
# - no clipping masks
# - no nested mask structures
# - splice handled as real split geometry
# - checker cells remain individually editable
# - useful object IDs for Illustrator / After Effects
#
# ============================================================


from html import escape
from typing import List, Tuple

from ai_edge_generator import (
    BACKGROUND,
    CompositionBlueprint,
    Primitive,
    create_ai_edge_blueprint,
    generate_ai_edge_pattern,
)


# ============================================================
# SVG HELPERS
# ============================================================

def fmt(
    value,
):

    if abs(
        value
        -
        round(
            value
        )
    ) < 0.000001:

        return str(
            int(
                round(
                    value
                )
            )
        )

    return (
        f"{value:.4f}"
        .rstrip("0")
        .rstrip(".")
    )


def svg_header(
    width,
    height,
):

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg '
        'xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{fmt(width)}" '
        f'height="{fmt(height)}" '
        f'viewBox="0 0 {fmt(width)} {fmt(height)}">\n'
    )


def svg_footer():

    return "</svg>\n"


# ============================================================
# SPLICE LINE
# ============================================================
#
# The PNG renderer conceptually divides the artwork with a
# diagonal line.
#
# We convert that into a mathematical half-plane.
#
# A point is considered "inside the splice side" when it falls
# on the alternate-color side of that diagonal.
#
# ============================================================

def splice_line_points(
    blueprint,
):

    width = blueprint.width
    height = blueprint.height
    position = blueprint.splice_position

    span = (
        width
        +
        height
    )

    if blueprint.splice_direction == "down":

        intercept = (
            position
            *
            span
            -
            width
        )

        p1 = (
            0.0,
            intercept,
        )

        p2 = (
            float(width),
            float(width)
            +
            intercept,
        )

    else:

        intercept = (
            position
            *
            span
        )

        p1 = (
            0.0,
            intercept,
        )

        p2 = (
            float(width),
            intercept
            -
            float(width),
        )

    return (
        p1,
        p2,
    )


def cross(
    ax,
    ay,
    bx,
    by,
):

    return (
        ax * by
        -
        ay * bx
    )


def point_side(
    point,
    line_a,
    line_b,
):

    px, py = point
    ax, ay = line_a
    bx, by = line_b

    return cross(
        bx - ax,
        by - ay,
        px - ax,
        py - ay,
    )


# ============================================================
# POLYGON CLIPPING AGAINST A HALF-PLANE
# ============================================================
#
# Sutherland-Hodgman clipping.
#
# This is what lets us split splice-crossed vector objects
# without using masks.
#
# ============================================================

def line_intersection(
    p1,
    p2,
    line_a,
    line_b,
):

    x1, y1 = p1
    x2, y2 = p2

    ax, ay = line_a
    bx, by = line_b

    segment_dx = (
        x2
        -
        x1
    )

    segment_dy = (
        y2
        -
        y1
    )

    line_dx = (
        bx
        -
        ax
    )

    line_dy = (
        by
        -
        ay
    )

    denominator = cross(
        segment_dx,
        segment_dy,
        line_dx,
        line_dy,
    )

    if abs(
        denominator
    ) < 0.0000001:

        return p2

    t = (
        cross(
            ax - x1,
            ay - y1,
            line_dx,
            line_dy,
        )
        /
        denominator
    )

    return (
        x1
        +
        t
        *
        segment_dx,

        y1
        +
        t
        *
        segment_dy,
    )


def clip_polygon_half_plane(
    polygon,
    line_a,
    line_b,
    keep_positive,
):

    if not polygon:

        return []

    output = []

    previous = polygon[
        -1
    ]

    previous_side = point_side(
        previous,
        line_a,
        line_b,
    )

    previous_inside = (
        previous_side
        >=
        0
        if keep_positive
        else
        previous_side
        <=
        0
    )

    for current in polygon:

        current_side = point_side(
            current,
            line_a,
            line_b,
        )

        current_inside = (
            current_side
            >=
            0
            if keep_positive
            else
            current_side
            <=
            0
        )

        if current_inside:

            if not previous_inside:

                output.append(
                    line_intersection(
                        previous,
                        current,
                        line_a,
                        line_b,
                    )
                )

            output.append(
                current
            )

        elif previous_inside:

            output.append(
                line_intersection(
                    previous,
                    current,
                    line_a,
                    line_b,
                )
            )

        previous = current
        previous_inside = (
            current_inside
        )

    return output


# ============================================================
# PRIMITIVE -> POLYGON
# ============================================================

def primitive_polygon(
    primitive,
):

    x0 = primitive.x
    y0 = primitive.y

    x1 = (
        primitive.x
        +
        primitive.w
    )

    y1 = (
        primitive.y
        +
        primitive.h
    )

    if primitive.type == "diamond":

        cx = (
            x0
            +
            x1
        ) / 2

        cy = (
            y0
            +
            y1
        ) / 2

        return [
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

    if primitive.type == "triangle_up":

        return [
            (
                (
                    x0
                    +
                    x1
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

    if primitive.type == "triangle_down":

        return [
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
                    x0
                    +
                    x1
                ) / 2,
                y1,
            ),
        ]

    return [
        (
            x0,
            y0,
        ),
        (
            x1,
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


# ============================================================
# SVG ELEMENT HELPERS
# ============================================================

def polygon_points_attribute(
    polygon,
):

    return " ".join(
        (
            fmt(x)
            +
            ","
            +
            fmt(y)
        )
        for x, y
        in polygon
    )


def polygon_svg(
    object_id,
    polygon,
    fill,
):

    if len(
        polygon
    ) < 3:

        return ""

    return (
        f'<polygon '
        f'id="{escape(object_id)}" '
        f'points="{polygon_points_attribute(polygon)}" '
        f'fill="{fill}" '
        f'stroke="none" />\n'
    )


def rect_svg(
    object_id,
    primitive,
    fill,
):

    return (
        f'<rect '
        f'id="{escape(object_id)}" '
        f'x="{fmt(primitive.x)}" '
        f'y="{fmt(primitive.y)}" '
        f'width="{fmt(primitive.w)}" '
        f'height="{fmt(primitive.h)}" '
        f'fill="{fill}" '
        f'stroke="none" />\n'
    )


def circle_svg(
    object_id,
    primitive,
    fill,
):

    cx = (
        primitive.x
        +
        primitive.w / 2
    )

    cy = (
        primitive.y
        +
        primitive.h / 2
    )

    radius = (
        min(
            primitive.w,
            primitive.h,
        )
        /
        2
    )

    return (
        f'<circle '
        f'id="{escape(object_id)}" '
        f'cx="{fmt(cx)}" '
        f'cy="{fmt(cy)}" '
        f'r="{fmt(radius)}" '
        f'fill="{fill}" '
        f'stroke="none" />\n'
    )


def capsule_svg(
    object_id,
    primitive,
    fill,
):

    radius = (
        min(
            primitive.w,
            primitive.h,
        )
        /
        2
    )

    return (
        f'<rect '
        f'id="{escape(object_id)}" '
        f'x="{fmt(primitive.x)}" '
        f'y="{fmt(primitive.y)}" '
        f'width="{fmt(primitive.w)}" '
        f'height="{fmt(primitive.h)}" '
        f'rx="{fmt(radius)}" '
        f'ry="{fmt(radius)}" '
        f'fill="{fill}" '
        f'stroke="none" />\n'
    )


# ============================================================
# CURVED SHAPES + SPLICE
# ============================================================
#
# Rectangles and polygonal motifs can be physically split
# cleanly with polygon clipping.
#
# Circles and capsules need true curved geometry.
#
# Rather than introduce clipping masks, we approximate only
# splice-crossed curved objects as high-resolution polygons.
#
# Non-spliced circles and pills stay native SVG <circle> /
# rounded <rect> objects.
#
# ============================================================

def circle_polygon(
    primitive,
    segments=48,
):

    import math

    cx = (
        primitive.x
        +
        primitive.w
        /
        2
    )

    cy = (
        primitive.y
        +
        primitive.h
        /
        2
    )

    radius = (
        min(
            primitive.w,
            primitive.h,
        )
        /
        2
    )

    result = []

    for index in range(
        segments
    ):

        angle = (
            math.pi
            *
            2
            *
            index
            /
            segments
        )

        result.append(
            (
                cx
                +
                math.cos(
                    angle
                )
                *
                radius,

                cy
                +
                math.sin(
                    angle
                )
                *
                radius,
            )
        )

    return result


def capsule_polygon(
    primitive,
    segments_per_cap=18,
):

    import math

    x = primitive.x
    y = primitive.y
    w = primitive.w
    h = primitive.h

    radius = (
        min(
            w,
            h,
        )
        /
        2
    )

    points = []

    if w >= h:

        left_cx = (
            x
            +
            radius
        )

        right_cx = (
            x
            +
            w
            -
            radius
        )

        cy = (
            y
            +
            h
            /
            2
        )

        for index in range(
            segments_per_cap + 1
        ):

            angle = (
                math.pi / 2
                +
                math.pi
                *
                index
                /
                segments_per_cap
            )

            points.append(
                (
                    left_cx
                    +
                    math.cos(
                        angle
                    )
                    *
                    radius,

                    cy
                    +
                    math.sin(
                        angle
                    )
                    *
                    radius,
                )
            )

        for index in range(
            segments_per_cap + 1
        ):

            angle = (
                -math.pi / 2
                +
                math.pi
                *
                index
                /
                segments_per_cap
            )

            points.append(
                (
                    right_cx
                    +
                    math.cos(
                        angle
                    )
                    *
                    radius,

                    cy
                    +
                    math.sin(
                        angle
                    )
                    *
                    radius,
                )
            )

    else:

        cx = (
            x
            +
            w
            /
            2
        )

        top_cy = (
            y
            +
            radius
        )

        bottom_cy = (
            y
            +
            h
            -
            radius
        )

        for index in range(
            segments_per_cap + 1
        ):

            angle = (
                math.pi
                +
                math.pi
                *
                index
                /
                segments_per_cap
            )

            points.append(
                (
                    cx
                    +
                    math.cos(
                        angle
                    )
                    *
                    radius,

                    top_cy
                    +
                    math.sin(
                        angle
                    )
                    *
                    radius,
                )
            )

        for index in range(
            segments_per_cap + 1
        ):

            angle = (
                0
                +
                math.pi
                *
                index
                /
                segments_per_cap
            )

            points.append(
                (
                    cx
                    +
                    math.cos(
                        angle
                    )
                    *
                    radius,

                    bottom_cy
                    +
                    math.sin(
                        angle
                    )
                    *
                    radius,
                )
            )

    return points


# ============================================================
# DOES SPLICE INTERSECT AN OBJECT?
# ============================================================

def polygon_crosses_splice(
    polygon,
    line_a,
    line_b,
):

    sides = [
        point_side(
            point,
            line_a,
            line_b,
        )
        for point
        in polygon
    ]

    has_positive = any(
        side > 0.00001
        for side in sides
    )

    has_negative = any(
        side < -0.00001
        for side in sides
    )

    return (
        has_positive
        and
        has_negative
    )


# ============================================================
# RENDER ONE PRIMITIVE
# ============================================================

def primitive_to_svg(
    primitive,
    blueprint,
):

    object_id = (
        primitive.id
    )

    # --------------------------------------------------------
    # NO SPLICE
    # --------------------------------------------------------

    if (
        not blueprint.splice_enabled
        or
        not primitive.splice_color
    ):

        if primitive.type == "rect":

            return rect_svg(
                object_id,
                primitive,
                primitive.color,
            )

        if primitive.type == "circle":

            return circle_svg(
                object_id,
                primitive,
                primitive.color,
            )

        if primitive.type == "capsule":

            return capsule_svg(
                object_id,
                primitive,
                primitive.color,
            )

        return polygon_svg(
            object_id,
            primitive_polygon(
                primitive
            ),
            primitive.color,
        )


    # --------------------------------------------------------
    # BUILD POLYGON FOR INTERSECTION TEST
    # --------------------------------------------------------

    if primitive.type == "circle":

        source_polygon = (
            circle_polygon(
                primitive
            )
        )

    elif primitive.type == "capsule":

        source_polygon = (
            capsule_polygon(
                primitive
            )
        )

    else:

        source_polygon = (
            primitive_polygon(
                primitive
            )
        )


    (
        line_a,
        line_b,
    ) = splice_line_points(
        blueprint
    )


    crosses = polygon_crosses_splice(
        source_polygon,
        line_a,
        line_b,
    )


    # --------------------------------------------------------
    # OBJECT DOES NOT CROSS SPLICE
    # --------------------------------------------------------

    if not crosses:

        center = (
            primitive.x
            +
            primitive.w
            /
            2,

            primitive.y
            +
            primitive.h
            /
            2,
        )

        side = point_side(
            center,
            line_a,
            line_b,
        )


        # Determine which side uses the splice color.
        #
        # This mirrors the half-plane direction used by the
        # PNG renderer's splice polygon.

        splice_side_positive = (
            blueprint.splice_direction
            ==
            "down"
        )


        use_splice = (
            side >= 0
            if splice_side_positive
            else side <= 0
        )


        fill = (
            primitive.splice_color
            if use_splice
            else primitive.color
        )


        if primitive.type == "rect":

            return rect_svg(
                object_id,
                primitive,
                fill,
            )

        if primitive.type == "circle":

            return circle_svg(
                object_id,
                primitive,
                fill,
            )

        if primitive.type == "capsule":

            return capsule_svg(
                object_id,
                primitive,
                fill,
            )

        return polygon_svg(
            object_id,
            source_polygon,
            fill,
        )


    # --------------------------------------------------------
    # OBJECT CROSSES SPLICE
    # --------------------------------------------------------
    #
    # Split into two REAL vector polygons.
    #
    # No clipping mask.
    #
    # Illustrator will simply see two neighboring editable
    # paths.
    #
    # --------------------------------------------------------

    splice_side_positive = (
        blueprint.splice_direction
        ==
        "down"
    )


    primary_polygon = (
        clip_polygon_half_plane(
            source_polygon,
            line_a,
            line_b,
            keep_positive=(
                not splice_side_positive
            ),
        )
    )


    splice_polygon_piece = (
        clip_polygon_half_plane(
            source_polygon,
            line_a,
            line_b,
            keep_positive=(
                splice_side_positive
            ),
        )
    )


    result = ""


    if len(
        primary_polygon
    ) >= 3:

        result += polygon_svg(
            object_id
            +
            "_A",

            primary_polygon,

            primitive.color,
        )


    if len(
        splice_polygon_piece
    ) >= 3:

        result += polygon_svg(
            object_id
            +
            "_B",

            splice_polygon_piece,

            primitive.splice_color,
        )


    return result


# ============================================================
# BLUEPRINT -> SVG
# ============================================================

def render_blueprint_svg(
    blueprint,
):

    parts = []

    parts.append(
        svg_header(
            blueprint.width,
            blueprint.height,
        )
    )


    # ========================================================
    # BACKGROUND
    # ========================================================

    parts.append(
        '<g id="BACKGROUND">\n'
    )

    parts.append(
        f'<rect '
        f'id="background" '
        f'x="0" '
        f'y="0" '
        f'width="{fmt(blueprint.width)}" '
        f'height="{fmt(blueprint.height)}" '
        f'fill="{BACKGROUND}" '
        f'stroke="none" />\n'
    )

    parts.append(
        "</g>\n"
    )


    # ========================================================
    # REGION LOOKUP
    # ========================================================

    region_map = {}

    for primitive in blueprint.primitives:

        region_map.setdefault(
            primitive.region_id,
            [],
        ).append(
            primitive
        )


    # ========================================================
    # ARTWORK
    # ========================================================

    parts.append(
        '<g id="ARTWORK">\n'
    )


    for region_id in sorted(
        region_map.keys()
    ):

        parts.append(
            f'<g '
            f'id="REGION_{region_id:03d}">\n'
        )


        for primitive in region_map[
            region_id
        ]:

            parts.append(
                primitive_to_svg(
                    primitive,
                    blueprint,
                )
            )


        parts.append(
            "</g>\n"
        )


    parts.append(
        "</g>\n"
    )


    parts.append(
        svg_footer()
    )


    return "".join(
        parts
    )


# ============================================================
# PUBLIC EXPORT FUNCTION
# ============================================================

def generate_ai_edge_vector(
    width=1200,
    height=1600,
    seed=48391027,
    negative_space=15,
    color_weights=None,
    shape_weights=None,
    splice_enabled=True,
):

    blueprint = create_ai_edge_blueprint(
        width=width,
        height=height,
        seed=seed,
        negative_space=negative_space,
        color_weights=color_weights,
        shape_weights=shape_weights,
        splice_enabled=splice_enabled,
    )


    svg_string = render_blueprint_svg(
        blueprint
    )


    metadata = {
        "version":
            "AI Edge Production Vector V3.1",

        "seed":
            blueprint.seed,

        "width":
            blueprint.width,

        "height":
            blueprint.height,

        "grid":
            blueprint.grid,

        "negative_space":
            blueprint.negative_space,

        "macro_omission":
            blueprint.macro_omission,

        "primitive_count":
            len(
                blueprint.primitives
            ),

        "region_count":
            len(
                blueprint.regions
            ),

        "splice_enabled":
            blueprint.splice_enabled,

        "gradients":
            False,

        "shimmer":
            False,

        "opacity_variation":
            False,
    }


    return (
        svg_string,
        metadata,
        blueprint,
    )


# ============================================================
# EXPORT FROM AN EXISTING BLUEPRINT
# ============================================================
#
# This is the function Streamlit will eventually use.
#
# We will generate ONE blueprint, then:
#
#     render_blueprint_png(blueprint)
#     render_blueprint_svg(blueprint)
#
# so there is literally no possibility of the two formats
# independently choosing different motifs/colors.
#
# ============================================================

def generate_vector_from_blueprint(
    blueprint,
):

    return render_blueprint_svg(
        blueprint
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    TEST_SEED = 48391027


    # Generate PNG + blueprint from the approved generator.

    (
        image,
        info,
        blueprint,
    ) = generate_ai_edge_pattern(
        width=1200,
        height=1600,

        seed=TEST_SEED,

        negative_space=15,

        color_weights={
            "Brown": 14,
            "Pink": 14,
            "Red": 18,
            "Yellow": 12,
            "Blue": 18,
            "Gray": 10,
            "Ice Blue": 14,
        },

        shape_weights={
            "Checkerboard": 7,
            "Lattice": 5,
            "Stair Step": 5,
            "Pills": 4,
        },

        splice_enabled=True,
    )


    # Render SVG from THE SAME blueprint.

    svg = generate_vector_from_blueprint(
        blueprint
    )


    png_filename = (
        f"ai_edge_vector_test_"
        f"{TEST_SEED}.png"
    )


    svg_filename = (
        f"ai_edge_vector_test_"
        f"{TEST_SEED}.svg"
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
            svg
        )


    print()

    print(
        "========================================"
    )

    print(
        " AI EDGE PRODUCTION VECTOR V3.1"
    )

    print(
        "========================================"
    )

    print(
        f" Seed:             "
        f"{TEST_SEED}"
    )

    print(
        f" PNG:              "
        f"{png_filename}"
    )

    print(
        f" Production SVG:   "
        f"{svg_filename}"
    )

    print(
        f" Primitives:       "
        f"{len(blueprint.primitives)}"
    )

    print(
        " Gradients:        OFF"
    )

    print(
        " Shimmer:          OFF"
    )

    print(
        " Masks:            NONE"
    )

    print(
        "========================================"
    )