# ============================================================
# AI EDGE GENERATOR V3.2
# Standalone AI-only pattern generator
# ============================================================
#
# CORE RULES
#
# - artwork constructed on a fixed 25 x 25 px grid
# - requested canvas may be ANY whole-pixel dimensions
# - complete 25 px cells bleed past the requested canvas
# - final PNG / SVG viewport crops the overflow
#
# - exact flat spot colors only
# - background ONLY #EAE7D9
# - no gradients
# - no shimmer
# - no opacity variation
# - no grain / texture
#
# - stable baseline footprint controlled by seed
# - calibrated negative-space control
# - adjustable color balance
# - adjustable shape dominance
# - two-color checkerboards
# - lattice / diamonds
# - stair steps
# - pills / capsules
# - AI architectural / factory motifs
# - ladder / circuit motifs
# - optional diagonal splice
#
# IMPORTANT
#
# This generator creates a CompositionBlueprint first.
# PNG and Production Vector both render from that SAME
# blueprint so they remain visually matched.
#
# ============================================================


import hashlib
import math
import random

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from PIL import Image, ImageDraw


# ============================================================
# BRAND SYSTEM
# ============================================================

GRID = 25

BACKGROUND = "#EAE7D9"

COLORS = {
    "Brown": "#4B190F",
    "Pink": "#F9BFF9",
    "Red": "#FF0015",
    "Yellow": "#FFFF8F",
    "Blue": "#416CA4",
    "Gray": "#A6B5C2",
    "Ice Blue": "#CBFEFF",
}


DEFAULT_COLOR_WEIGHTS = {
    "Brown": 14,
    "Pink": 14,
    "Red": 14,
    "Yellow": 14,
    "Blue": 16,
    "Gray": 14,
    "Ice Blue": 14,
}


DEFAULT_SHAPE_WEIGHTS = {
    "Checkerboard": 5,
    "Lattice": 5,
    "Stair Step": 5,
    "Pills": 5,
}


# These baseline motifs are deliberately not exposed as
# controls. They preserve the AI Edge identity.

BASE_FACTORY_WEIGHT = 3.0
BASE_LADDER_WEIGHT = 2.5
BASE_CIRCLES_WEIGHT = 1.5


# ============================================================
# NEGATIVE SPACE CALIBRATION
# ============================================================
#
# The motifs themselves naturally expose some background.
#
# Therefore:
#
# 0–15% = dense composition; no complete macro regions removed
#
# Above 15%, complete macro regions are progressively omitted.
#
# ============================================================

NATURAL_NEGATIVE_SPACE_ALLOWANCE = 15.0


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Region:

    id: int

    # Grid coordinates, not pixels.
    x: int
    y: int
    w: int
    h: int

    negative_score: float
    motif_seed: int
    color_seed: int


@dataclass
class Primitive:

    id: str

    type: str

    # Pixel coordinates.
    #
    # These are allowed to extend past blueprint.width /
    # blueprint.height. The final render crops the overflow.

    x: float
    y: float
    w: float
    h: float

    color: str

    splice_color: Optional[str] = None

    region_id: int = 0
    motif: str = ""


@dataclass
class CompositionBlueprint:

    # Requested output canvas.
    width: int
    height: int

    grid: int
    seed: int
    background: str

    # Full internal grid coverage.
    grid_cols: int
    grid_rows: int
    bleed_width: int
    bleed_height: int

    negative_space: float
    macro_omission: float

    color_weights: Dict[str, float]
    shape_weights: Dict[str, float]

    splice_enabled: bool
    splice_direction: str
    splice_position: float

    regions: List[Region]
    omitted_region_ids: List[int]
    primitives: List[Primitive]


# ============================================================
# GENERAL HELPERS
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


def normalize_weights(
    incoming,
    defaults,
    minimum=0.0,
):

    incoming = incoming or {}

    result = {}

    for name, default in defaults.items():

        try:

            value = float(
                incoming.get(
                    name,
                    default,
                )
            )

        except Exception:

            value = float(
                default
            )

        result[name] = max(
            minimum,
            value,
        )

    if sum(
        result.values()
    ) <= 0:

        return {
            name: float(value)
            for name, value
            in defaults.items()
        }

    return result


def stable_integer(
    *parts,
):

    key = "|".join(
        str(part)
        for part in parts
    )

    digest = hashlib.sha256(
        key.encode(
            "utf-8"
        )
    ).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )


def stable_float(
    *parts,
):

    integer = stable_integer(
        *parts
    )

    return (
        integer
        /
        float(
            2 ** 64 - 1
        )
    )


def make_rng(
    *parts,
):

    return random.Random(
        stable_integer(
            *parts
        )
    )


def weighted_choice(
    rng,
    weight_dict,
):

    names = list(
        weight_dict.keys()
    )

    weights = [
        max(
            0.0,
            float(
                weight_dict[name]
            ),
        )
        for name in names
    ]

    if sum(
        weights
    ) <= 0:

        weights = [
            1.0
            for _ in names
        ]

    return rng.choices(
        names,
        weights=weights,
        k=1,
    )[0]


def choose_secondary_color(
    rng,
    first_name,
    color_weights,
):

    alternatives = {
        name: weight
        for name, weight
        in color_weights.items()
        if (
            name != first_name
            and
            weight > 0
        )
    }

    if not alternatives:

        alternatives = {
            name: 1
            for name in COLORS
            if name != first_name
        }

    return weighted_choice(
        rng,
        alternatives,
    )


# ============================================================
# BASELINE FOOTPRINT
# ============================================================
#
# Creates a tiled set of macro regions on the 25 px grid.
#
# For arbitrary requested dimensions, cols / rows are CEILED:
#
# 1213 px wide
# -> ceil(1213 / 25)
# -> 49 cells
# -> 1225 px internal pattern width
# -> final image crops to 1213 px
#
# ============================================================

def build_baseline_regions(
    cols,
    rows,
    seed,
):

    rng = make_rng(
        seed,
        "baseline",
    )

    raw_regions = []

    MIN_REGION = 3
    MAX_REGION = 10


    def split_region(
        x,
        y,
        w,
        h,
    ):

        should_split = (
            w > MAX_REGION
            or
            h > MAX_REGION
            or
            (
                w * h > 48
                and
                rng.random() < 0.72
            )
        )


        if not should_split:

            raw_regions.append(
                (
                    x,
                    y,
                    w,
                    h,
                )
            )

            return


        split_vertical = (
            w >= h
        )


        if rng.random() < 0.22:

            split_vertical = (
                not split_vertical
            )


        if split_vertical:

            possible = [
                position
                for position
                in range(
                    MIN_REGION,
                    w - MIN_REGION + 1,
                )
            ]


            if not possible:

                raw_regions.append(
                    (
                        x,
                        y,
                        w,
                        h,
                    )
                )

                return


            split = rng.choice(
                possible
            )


            split_region(
                x,
                y,
                split,
                h,
            )


            split_region(
                x + split,
                y,
                w - split,
                h,
            )


        else:

            possible = [
                position
                for position
                in range(
                    MIN_REGION,
                    h - MIN_REGION + 1,
                )
            ]


            if not possible:

                raw_regions.append(
                    (
                        x,
                        y,
                        w,
                        h,
                    )
                )

                return


            split = rng.choice(
                possible
            )


            split_region(
                x,
                y,
                w,
                split,
            )


            split_region(
                x,
                y + split,
                w,
                h - split,
            )


    split_region(
        0,
        0,
        cols,
        rows,
    )


    regions = []


    for index, (
        x,
        y,
        w,
        h,
    ) in enumerate(
        raw_regions
    ):

        region_id = (
            index + 1
        )


        regions.append(
            Region(
                id=region_id,

                x=x,
                y=y,
                w=w,
                h=h,

                negative_score=stable_float(
                    seed,
                    "negative",
                    x,
                    y,
                    w,
                    h,
                ),

                motif_seed=stable_integer(
                    seed,
                    "motif",
                    x,
                    y,
                    w,
                    h,
                ),

                color_seed=stable_integer(
                    seed,
                    "color",
                    x,
                    y,
                    w,
                    h,
                ),
            )
        )


    return regions


# ============================================================
# NEGATIVE SPACE
# ============================================================

def calculate_macro_omission(
    negative_space,
):

    requested = clamp(
        float(
            negative_space
        ),
        0.0,
        60.0,
    )

    return max(
        0.0,
        requested
        -
        NATURAL_NEGATIVE_SPACE_ALLOWANCE,
    )


def choose_omitted_regions(
    regions,
    cols,
    rows,
    negative_space,
):

    macro_omission = (
        calculate_macro_omission(
            negative_space
        )
    )


    if macro_omission <= 0:

        return (
            set(),
            0.0,
        )


    total_cells = (
        cols
        *
        rows
    )


    target_cells = (
        total_cells
        *
        (
            macro_omission
            /
            100.0
        )
    )


    ordered = sorted(
        regions,
        key=lambda region:
            region.negative_score,
    )


    omitted = set()

    omitted_cells = 0


    for region in ordered:

        area = (
            region.w
            *
            region.h
        )


        without_region_error = abs(
            target_cells
            -
            omitted_cells
        )


        with_region_error = abs(
            target_cells
            -
            (
                omitted_cells
                +
                area
            )
        )


        if omitted_cells < target_cells:

            if (
                with_region_error
                <=
                without_region_error
                or
                omitted_cells
                <
                target_cells * 0.72
            ):

                omitted.add(
                    region.id
                )

                omitted_cells += (
                    area
                )


        if omitted_cells >= target_cells:

            break


    actual_omission = (
        omitted_cells
        /
        total_cells
        *
        100.0
    )


    return (
        omitted,
        actual_omission,
    )


# ============================================================
# MOTIF CHOICE
# ============================================================

def choose_region_motif(
    region,
    shape_weights,
):

    rng = random.Random(
        region.motif_seed
    )


    checker = shape_weights[
        "Checkerboard"
    ]

    lattice = shape_weights[
        "Lattice"
    ]

    stairs = shape_weights[
        "Stair Step"
    ]

    pills = shape_weights[
        "Pills"
    ]


    weights = {

        "checker":
            checker
            *
            1.4,

        "lattice":
            lattice
            *
            1.15,

        "stair":
            stairs
            *
            1.15,

        "pills":
            pills
            *
            1.05,

        "factory":
            BASE_FACTORY_WEIGHT,

        "ladder":
            BASE_LADDER_WEIGHT,

        "circles":
            BASE_CIRCLES_WEIGHT,
    }


    return weighted_choice(
        rng,
        weights,
    )


# ============================================================
# REGION COLORS
# ============================================================

def choose_region_colors(
    region,
    color_weights,
):

    rng = random.Random(
        region.color_seed
    )


    primary_name = weighted_choice(
        rng,
        color_weights,
    )


    secondary_name = (
        choose_secondary_color(
            rng,
            primary_name,
            color_weights,
        )
    )


    splice_name = (
        choose_secondary_color(
            rng,
            primary_name,
            color_weights,
        )
    )


    return (
        COLORS[
            primary_name
        ],

        COLORS[
            secondary_name
        ],

        COLORS[
            splice_name
        ],
    )


# ============================================================
# PRIMITIVE CREATOR
# ============================================================

class PrimitiveBuilder:

    def __init__(
        self,
        region,
        motif,
        splice_color,
    ):

        self.region = region
        self.motif = motif
        self.splice_color = splice_color

        self.index = 0
        self.items = []


    def add(
        self,
        primitive_type,
        x_cells,
        y_cells,
        w_cells,
        h_cells,
        color,
    ):

        self.index += 1


        self.items.append(
            Primitive(
                id=(
                    f"{self.motif}_"
                    f"{self.region.id:03d}_"
                    f"{self.index:04d}"
                ),

                type=primitive_type,

                x=(
                    x_cells
                    *
                    GRID
                ),

                y=(
                    y_cells
                    *
                    GRID
                ),

                w=(
                    w_cells
                    *
                    GRID
                ),

                h=(
                    h_cells
                    *
                    GRID
                ),

                color=color,

                splice_color=(
                    self.splice_color
                ),

                region_id=(
                    self.region.id
                ),

                motif=(
                    self.motif
                ),
            )
        )


# ============================================================
# MOTIF: CHECKERBOARD
# ============================================================

def build_checker(
    region,
    color_a,
    color_b,
    splice_color,
):

    builder = PrimitiveBuilder(
        region,
        "checker",
        splice_color,
    )


    for row in range(
        region.h
    ):

        for col in range(
            region.w
        ):

            color = (
                color_a
                if (
                    (
                        row
                        +
                        col
                    )
                    %
                    2
                    ==
                    0
                )
                else
                color_b
            )


            builder.add(
                "rect",

                region.x
                +
                col,

                region.y
                +
                row,

                1,
                1,

                color,
            )


    return builder.items


# ============================================================
# MOTIF: LATTICE
# ============================================================

def build_lattice(
    region,
    color_a,
    color_b,
    splice_color,
):

    builder = PrimitiveBuilder(
        region,
        "lattice",
        splice_color,
    )


    for row in range(
        region.h
    ):

        for col in range(
            region.w
        ):

            color = (
                color_a
                if (
                    (
                        (
                            row
                            //
                            2
                        )
                        +
                        (
                            col
                            //
                            2
                        )
                    )
                    %
                    2
                    ==
                    0
                )
                else
                color_b
            )


            builder.add(
                "diamond",

                region.x
                +
                col,

                region.y
                +
                row,

                1,
                1,

                color,
            )


    return builder.items


# ============================================================
# MOTIF: CIRCLES
# ============================================================

def build_circles(
    region,
    color_a,
    color_b,
    splice_color,
):

    builder = PrimitiveBuilder(
        region,
        "circles",
        splice_color,
    )


    for row in range(
        region.h
    ):

        for col in range(
            region.w
        ):

            color = (
                color_a
                if (
                    (
                        row
                        +
                        col
                    )
                    %
                    3
                    !=
                    0
                )
                else
                color_b
            )


            builder.add(
                "circle",

                region.x
                +
                col,

                region.y
                +
                row,

                1,
                1,

                color,
            )


    return builder.items


# ============================================================
# MOTIF: PILLS / CAPSULES
# ============================================================

def build_pills(
    region,
    color_a,
    color_b,
    splice_color,
    seed,
):

    builder = PrimitiveBuilder(
        region,
        "pills",
        splice_color,
    )


    rng = make_rng(
        seed,
        "pills",
        region.id,
    )


    horizontal = (
        region.w
        >=
        region.h
    )


    if rng.random() < 0.25:

        horizontal = (
            not horizontal
        )


    if horizontal:

        row = 0


        while row < region.h:

            col = 0


            while col < region.w:

                remaining = (
                    region.w
                    -
                    col
                )


                length = min(
                    remaining,

                    rng.choice(
                        [
                            2,
                            2,
                            3,
                            3,
                            4,
                        ]
                    ),
                )


                color = (
                    color_a
                    if rng.random() < 0.68
                    else color_b
                )


                builder.add(
                    "capsule",

                    region.x
                    +
                    col,

                    region.y
                    +
                    row,

                    length,
                    1,

                    color,
                )


                col += (
                    length
                )


            row += 1


    else:

        col = 0


        while col < region.w:

            row = 0


            while row < region.h:

                remaining = (
                    region.h
                    -
                    row
                )


                length = min(
                    remaining,

                    rng.choice(
                        [
                            2,
                            2,
                            3,
                            3,
                            4,
                        ]
                    ),
                )


                color = (
                    color_a
                    if rng.random() < 0.68
                    else color_b
                )


                builder.add(
                    "capsule",

                    region.x
                    +
                    col,

                    region.y
                    +
                    row,

                    1,
                    length,

                    color,
                )


                row += (
                    length
                )


            col += 1


    return builder.items


# ============================================================
# MOTIF: STAIR STEP
# ============================================================

def build_stair(
    region,
    color_a,
    color_b,
    splice_color,
    seed,
):

    builder = PrimitiveBuilder(
        region,
        "stair",
        splice_color,
    )


    rng = make_rng(
        seed,
        "stair",
        region.id,
    )


    direction = rng.choice(
        [
            "down_right",
            "down_left",
        ]
    )


    thickness = rng.choice(
        [
            1,
            1,
            2,
        ]
    )


    for row in range(
        region.h
    ):

        step = (
            row
            //
            thickness
        )


        if direction == "down_right":

            start = min(
                region.w
                -
                1,

                step,
            )


        else:

            start = max(
                0,

                region.w
                -
                1
                -
                step,
            )


        if direction == "down_right":

            run = (
                region.w
                -
                start
            )


            if run > 0:

                color = (
                    color_a
                    if row % 3 != 2
                    else color_b
                )


                builder.add(
                    "rect",

                    region.x
                    +
                    start,

                    region.y
                    +
                    row,

                    run,
                    1,

                    color,
                )


        else:

            run = (
                start
                +
                1
            )


            if run > 0:

                color = (
                    color_a
                    if row % 3 != 2
                    else color_b
                )


                builder.add(
                    "rect",

                    region.x,

                    region.y
                    +
                    row,

                    run,
                    1,

                    color,
                )


    return builder.items


# ============================================================
# MOTIF: FACTORY / ARCHITECTURAL
# ============================================================

def build_factory(
    region,
    color_a,
    color_b,
    splice_color,
    seed,
):

    builder = PrimitiveBuilder(
        region,
        "factory",
        splice_color,
    )


    rng = make_rng(
        seed,
        "factory",
        region.id,
    )


    base_rows = max(
        1,
        region.h
        //
        2,
    )


    builder.add(
        "rect",

        region.x,

        region.y
        +
        region.h
        -
        base_rows,

        region.w,
        base_rows,

        color_a,
    )


    for col in range(
        0,
        region.w,
        2,
    ):

        builder.add(
            "triangle_up",

            region.x
            +
            col,

            region.y
            +
            region.h
            -
            base_rows
            -
            1,

            1,
            1,

            color_a,
        )


    tower_count = max(
        1,

        min(
            3,
            region.w
            //
            3,
        ),
    )


    tower_positions = list(
        range(
            region.w
        )
    )


    rng.shuffle(
        tower_positions
    )


    for index in range(
        tower_count
    ):

        col = tower_positions[
            index
        ]


        tower_height = rng.randint(
            1,

            max(
                1,
                region.h
                -
                base_rows,
            ),
        )


        builder.add(
            "rect",

            region.x
            +
            col,

            region.y
            +
            region.h
            -
            base_rows
            -
            tower_height,

            1,
            tower_height,

            color_b,
        )


    return builder.items


# ============================================================
# MOTIF: LADDER / CIRCUIT
# ============================================================

def build_ladder(
    region,
    color_a,
    color_b,
    splice_color,
    seed,
):

    builder = PrimitiveBuilder(
        region,
        "ladder",
        splice_color,
    )


    rng = make_rng(
        seed,
        "ladder",
        region.id,
    )


    vertical = (
        region.h
        >=
        region.w
    )


    if rng.random() < 0.2:

        vertical = (
            not vertical
        )


    if vertical:

        spine_col = (
            region.w
            //
            2
        )


        builder.add(
            "rect",

            region.x
            +
            spine_col,

            region.y,

            1,
            region.h,

            color_a,
        )


        for row in range(
            0,
            region.h,
            2,
        ):

            direction_left = (
                row
                %
                4
                ==
                0
            )


            if direction_left:

                width = (
                    spine_col
                    +
                    1
                )


                builder.add(
                    "rect",

                    region.x,

                    region.y
                    +
                    row,

                    width,
                    1,

                    color_b,
                )


            else:

                width = (
                    region.w
                    -
                    spine_col
                )


                builder.add(
                    "rect",

                    region.x
                    +
                    spine_col,

                    region.y
                    +
                    row,

                    width,
                    1,

                    color_b,
                )


    else:

        spine_row = (
            region.h
            //
            2
        )


        builder.add(
            "rect",

            region.x,

            region.y
            +
            spine_row,

            region.w,
            1,

            color_a,
        )


        for col in range(
            0,
            region.w,
            2,
        ):

            direction_up = (
                col
                %
                4
                ==
                0
            )


            if direction_up:

                height = (
                    spine_row
                    +
                    1
                )


                builder.add(
                    "rect",

                    region.x
                    +
                    col,

                    region.y,

                    1,
                    height,

                    color_b,
                )


            else:

                height = (
                    region.h
                    -
                    spine_row
                )


                builder.add(
                    "rect",

                    region.x
                    +
                    col,

                    region.y
                    +
                    spine_row,

                    1,
                    height,

                    color_b,
                )


    return builder.items


# ============================================================
# BUILD ONE REGION
# ============================================================

def build_region_primitives(
    region,
    motif,
    color_a,
    color_b,
    splice_color,
    seed,
):

    if motif == "checker":

        return build_checker(
            region,
            color_a,
            color_b,
            splice_color,
        )


    if motif == "lattice":

        return build_lattice(
            region,
            color_a,
            color_b,
            splice_color,
        )


    if motif == "pills":

        return build_pills(
            region,
            color_a,
            color_b,
            splice_color,
            seed,
        )


    if motif == "stair":

        return build_stair(
            region,
            color_a,
            color_b,
            splice_color,
            seed,
        )


    if motif == "factory":

        return build_factory(
            region,
            color_a,
            color_b,
            splice_color,
            seed,
        )


    if motif == "ladder":

        return build_ladder(
            region,
            color_a,
            color_b,
            splice_color,
            seed,
        )


    return build_circles(
        region,
        color_a,
        color_b,
        splice_color,
    )


# ============================================================
# CREATE COMPOSITION BLUEPRINT
# ============================================================

def create_ai_edge_blueprint(
    width,
    height,
    seed,
    negative_space=15,
    color_weights=None,
    shape_weights=None,
    splice_enabled=True,
):

    width = int(
        width
    )

    height = int(
        height
    )

    seed = int(
        seed
    )


    if width <= 0 or height <= 0:

        raise ValueError(
            "Width and height must both be greater than zero."
        )


    negative_space = clamp(
        float(
            negative_space
        ),
        0,
        60,
    )


    color_weights = normalize_weights(
        color_weights,
        DEFAULT_COLOR_WEIGHTS,
        minimum=0.0,
    )


    shape_weights = normalize_weights(
        shape_weights,
        DEFAULT_SHAPE_WEIGHTS,
        minimum=1.0,
    )


    # ========================================================
    # V3.2 — ARBITRARY CANVAS DIMENSIONS
    # ========================================================
    #
    # Always create enough full 25 px cells to cover the
    # requested output.
    #
    # Example:
    #
    # width = 1213
    #
    # ceil(1213 / 25) = 49 cells
    #
    # 49 x 25 = 1225 px internal artwork
    #
    # Final output remains exactly 1213 px wide.
    #
    # ========================================================

    cols = int(
        math.ceil(
            width
            /
            GRID
        )
    )

    rows = int(
        math.ceil(
            height
            /
            GRID
        )
    )


    bleed_width = (
        cols
        *
        GRID
    )

    bleed_height = (
        rows
        *
        GRID
    )


    regions = build_baseline_regions(
        cols,
        rows,
        seed,
    )


    (
        omitted_region_ids,
        actual_macro_omission,
    ) = choose_omitted_regions(
        regions,
        cols,
        rows,
        negative_space,
    )


    # ========================================================
    # SPLICE
    # ========================================================
    #
    # Build splice using the bleed dimensions rather than the
    # cropped dimensions so the splice behaves as though the
    # pattern continues beyond the canvas edge.
    #
    # ========================================================

    splice_rng = make_rng(
        seed,
        "splice",
    )


    splice_direction = (
        "down"
        if splice_rng.random() < 0.5
        else "up"
    )


    splice_position = splice_rng.uniform(
        0.28,
        0.72,
    )


    primitives = []


    for region in regions:

        if (
            region.id
            in
            omitted_region_ids
        ):

            continue


        motif = choose_region_motif(
            region,
            shape_weights,
        )


        (
            color_a,
            color_b,
            splice_color,
        ) = choose_region_colors(
            region,
            color_weights,
        )


        region_primitives = (
            build_region_primitives(
                region,
                motif,
                color_a,
                color_b,
                splice_color,
                seed,
            )
        )


        primitives.extend(
            region_primitives
        )


    return CompositionBlueprint(
        width=width,
        height=height,

        grid=GRID,

        seed=seed,

        background=BACKGROUND,

        grid_cols=cols,
        grid_rows=rows,

        bleed_width=bleed_width,
        bleed_height=bleed_height,

        negative_space=(
            negative_space
        ),

        macro_omission=(
            actual_macro_omission
        ),

        color_weights=(
            color_weights
        ),

        shape_weights=(
            shape_weights
        ),

        splice_enabled=(
            bool(
                splice_enabled
            )
        ),

        splice_direction=(
            splice_direction
        ),

        splice_position=(
            splice_position
        ),

        regions=regions,

        omitted_region_ids=sorted(
            list(
                omitted_region_ids
            )
        ),

        primitives=primitives,
    )


# ============================================================
# SPLICE GEOMETRY
# ============================================================

def splice_polygon(
    width,
    height,
    direction,
    position,
):

    span = (
        width
        +
        height
    )


    if direction == "down":

        intercept = (
            position
            *
            span
            -
            width
        )


        return [
            (
                0,
                intercept,
            ),

            (
                width,
                width
                +
                intercept,
            ),

            (
                width,
                height
                +
                width,
            ),

            (
                0,
                height
                +
                width,
            ),
        ]


    intercept = (
        position
        *
        span
    )


    return [
        (
            0,
            -height,
        ),

        (
            width,
            -height,
        ),

        (
            width,
            intercept
            -
            width,
        ),

        (
            0,
            intercept,
        ),
    ]


# ============================================================
# DRAW PRIMITIVE INTO MASK
# ============================================================

def draw_primitive_mask(
    draw,
    primitive,
    scale=1,
):

    x0 = (
        primitive.x
        *
        scale
    )

    y0 = (
        primitive.y
        *
        scale
    )

    x1 = (
        primitive.x
        +
        primitive.w
    ) * scale

    y1 = (
        primitive.y
        +
        primitive.h
    ) * scale


    bbox = [
        x0,
        y0,
        x1,
        y1,
    ]


    if primitive.type == "rect":

        draw.rectangle(
            bbox,
            fill=255,
        )

        return


    if primitive.type == "circle":

        size = min(
            primitive.w,
            primitive.h,
        ) * scale


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


        radius = (
            size
            /
            2
        )


        draw.ellipse(
            [
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ],
            fill=255,
        )

        return


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


        draw.polygon(
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
            fill=255,
        )

        return


    if primitive.type == "triangle_up":

        draw.polygon(
            [
                (
                    (
                        x0
                        +
                        x1
                    )
                    /
                    2,

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
            fill=255,
        )

        return


    if primitive.type == "triangle_down":

        draw.polygon(
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
                        x0
                        +
                        x1
                    )
                    /
                    2,

                    y1,
                ),
            ],
            fill=255,
        )

        return


    if primitive.type == "capsule":

        radius = (
            min(
                primitive.w,
                primitive.h,
            )
            *
            scale
            /
            2
        )


        draw.rounded_rectangle(
            bbox,
            radius=radius,
            fill=255,
        )

        return


    draw.rectangle(
        bbox,
        fill=255,
    )


# ============================================================
# RENDER BLUEPRINT TO PNG
# ============================================================

def render_blueprint_png(
    blueprint,
):

    SCALE = 2


    # ========================================================
    # RENDER BLEED CANVAS
    # ========================================================
    #
    # Artwork is rendered on the complete 25 px construction
    # grid first.
    #
    # ========================================================

    render_width = (
        blueprint.bleed_width
    )

    render_height = (
        blueprint.bleed_height
    )


    canvas = Image.new(
        "RGB",

        (
            render_width
            *
            SCALE,

            render_height
            *
            SCALE,
        ),

        blueprint.background,
    )


    splice_mask = None


    if blueprint.splice_enabled:

        splice_mask = Image.new(
            "L",
            canvas.size,
            0,
        )


        splice_draw = ImageDraw.Draw(
            splice_mask
        )


        polygon = splice_polygon(
            render_width,
            render_height,
            blueprint.splice_direction,
            blueprint.splice_position,
        )


        polygon = [
            (
                x * SCALE,
                y * SCALE,
            )
            for x, y
            in polygon
        ]


        splice_draw.polygon(
            polygon,
            fill=255,
        )


    # ========================================================
    # DRAW PRIMITIVES
    # ========================================================

    for primitive in blueprint.primitives:

        shape_mask = Image.new(
            "L",
            canvas.size,
            0,
        )


        shape_draw = ImageDraw.Draw(
            shape_mask
        )


        draw_primitive_mask(
            shape_draw,
            primitive,
            scale=SCALE,
        )


        primary_layer = Image.new(
            "RGB",
            canvas.size,
            primitive.color,
        )


        canvas.paste(
            primary_layer,
            (
                0,
                0,
            ),
            shape_mask,
        )


        if (
            blueprint.splice_enabled
            and
            primitive.splice_color
            and
            splice_mask is not None
        ):

            intersection = Image.new(
                "L",
                canvas.size,
                0,
            )


            shape_pixels = (
                shape_mask.load()
            )

            splice_pixels = (
                splice_mask.load()
            )

            intersection_pixels = (
                intersection.load()
            )


            x0 = max(
                0,
                int(
                    primitive.x
                    *
                    SCALE
                ),
            )


            y0 = max(
                0,
                int(
                    primitive.y
                    *
                    SCALE
                ),
            )


            x1 = min(
                canvas.width,

                int(
                    (
                        primitive.x
                        +
                        primitive.w
                    )
                    *
                    SCALE
                )
                +
                2,
            )


            y1 = min(
                canvas.height,

                int(
                    (
                        primitive.y
                        +
                        primitive.h
                    )
                    *
                    SCALE
                )
                +
                2,
            )


            for y in range(
                y0,
                y1,
            ):

                for x in range(
                    x0,
                    x1,
                ):

                    if (
                        shape_pixels[
                            x,
                            y
                        ]
                        and
                        splice_pixels[
                            x,
                            y
                        ]
                    ):

                        intersection_pixels[
                            x,
                            y
                        ] = 255


            splice_layer = Image.new(
                "RGB",
                canvas.size,
                primitive.splice_color,
            )


            canvas.paste(
                splice_layer,
                (
                    0,
                    0,
                ),
                intersection,
            )


    # ========================================================
    # DOWNSAMPLE BLEED ARTWORK
    # ========================================================

    canvas = canvas.resize(
        (
            render_width,
            render_height,
        ),
        Image.Resampling.LANCZOS,
    )


    # ========================================================
    # CROP TO REQUESTED ARTBOARD
    # ========================================================
    #
    # This is the V3.2 behavior:
    #
    # Complete 25 px cells continue past the crop.
    #
    # The art director gets exactly the requested pixel size.
    #
    # ========================================================

    canvas = canvas.crop(
        (
            0,
            0,
            blueprint.width,
            blueprint.height,
        )
    )


    return canvas


# ============================================================
# PUBLIC GENERATOR
# ============================================================

def generate_ai_edge_pattern(
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


    image = render_blueprint_png(
        blueprint
    )


    metadata = {
        "version":
            "AI Edge V3.2",

        "seed":
            blueprint.seed,

        "width":
            blueprint.width,

        "height":
            blueprint.height,

        "grid":
            GRID,

        "grid_cols":
            blueprint.grid_cols,

        "grid_rows":
            blueprint.grid_rows,

        "bleed_width":
            blueprint.bleed_width,

        "bleed_height":
            blueprint.bleed_height,

        "background":
            BACKGROUND,

        "negative_space":
            blueprint.negative_space,

        "macro_omission":
            blueprint.macro_omission,

        "region_count":
            len(
                blueprint.regions
            ),

        "omitted_region_count":
            len(
                blueprint.omitted_region_ids
            ),

        "primitive_count":
            len(
                blueprint.primitives
            ),

        "splice_enabled":
            blueprint.splice_enabled,

        "splice_direction":
            blueprint.splice_direction,

        "splice_position":
            blueprint.splice_position,

        "color_weights":
            blueprint.color_weights,

        "shape_weights":
            blueprint.shape_weights,
    }


    return (
        image,
        metadata,
        blueprint,
    )


# ============================================================
# BLUEPRINT -> DICTIONARY
# ============================================================

def blueprint_to_dict(
    blueprint,
):

    return asdict(
        blueprint
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    TEST_SEED = 48391027


    # Deliberately NOT multiples of 25.
    #
    # This confirms that V3.2 is doing the bleed/crop behavior.

    TEST_WIDTH = 1213
    TEST_HEIGHT = 743


    image, info, blueprint = (
        generate_ai_edge_pattern(
            width=TEST_WIDTH,

            height=TEST_HEIGHT,

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
    )


    filename = (
        f"ai_edge_v3_2_"
        f"{TEST_SEED}_"
        f"{TEST_WIDTH}x"
        f"{TEST_HEIGHT}.png"
    )


    image.save(
        filename
    )


    print()

    print(
        "========================================"
    )

    print(
        " AI EDGE V3.2"
    )

    print(
        "========================================"
    )

    print(
        f" Seed:               "
        f"{info['seed']}"
    )

    print(
        f" Requested size:     "
        f"{info['width']} x "
        f"{info['height']}"
    )

    print(
        f" Construction grid:  "
        f"{info['grid_cols']} x "
        f"{info['grid_rows']} cells"
    )

    print(
        f" Internal bleed:     "
        f"{info['bleed_width']} x "
        f"{info['bleed_height']} px"
    )

    print(
        f" Grid:               "
        f"{info['grid']} px"
    )

    print(
        f" Negative space:     "
        f"{info['negative_space']}%"
    )

    print(
        f" Regions:            "
        f"{info['region_count']}"
    )

    print(
        f" Primitives:         "
        f"{info['primitive_count']}"
    )

    print(
        f" Output file:        "
        f"{filename}"
    )

    print(
        " Gradients:          OFF"
    )

    print(
        " Shimmer:            OFF"
    )

    print(
        " Grain:              OFF"
    )

    print(
        "========================================"
    )