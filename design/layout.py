"""
Single source of truth for the Puri home-cum-hotel design.

Every dimension is in FEET. Origin = south-west corner of the plot.
+x runs east, +y runs north (the road is on the north side), +z is up.

Both the Blender builder (generator/build_model.py) and the 2D plan
generator (generator/plans.py) read this file, so change a number here
and rebuild to update everything.
"""

# --------------------------------------------------------------------------
# Plot and levels
# --------------------------------------------------------------------------
PLOT_W = 30.0          # east-west (road frontage)
PLOT_D = 40.0          # north-south
ROAD_SIDE = "north"

EXT_T = 0.75           # 9" external / core walls
INT_T = 0.375          # 4.5" internal partitions
COL = 1.0              # 12" x 12" RCC columns (sized for G+3)
SLAB = 0.75            # slab + floor finish
BEAM_D = 1.0           # drop beam depth below slab (visible in stilt)

ROAD = 0.0             # road / site level
GF = 1.0               # ground (stilt) floor finished level - 12" plinth
FF = 11.5              # first floor finished level
ROOF = 22.0            # roof terrace level (= future second floor level)
FLOOR_TO_FLOOR = 10.5
PARAPET_H = 3.0
MUMTY_H = 8.0          # stair head-room room on the roof (removable later)

# Stair: dog-leg, 2 flights per storey, 10 risers per flight
RISER = FLOOR_TO_FLOOR / 20.0      # 0.525 ft = 6.3"
TREAD = 10.0 / 12.0                # 10"
STAIR = dict(
    box=(22.0, 25.0, 30.0, 40.0),  # wall centre-lines (x0, y0, x1, y1)
    inner=(22.375, 25.375, 29.625, 39.625),
    west_flight=(22.375, 25.875),  # flight 1 (goes south)
    east_flight=(26.125, 29.625),  # flight 2 (goes north)
    floor_landing_y=36.2,          # north landing (floor level) starts here
    mid_landing_y=36.2 - 9 * TREAD,  # 28.7 - mid landing ends here
)

# --------------------------------------------------------------------------
# Structure: RCC columns (centre points) - same grid on every floor so the
# building can grow to G+3. Starter bars are left above the roof.
# --------------------------------------------------------------------------
COLUMNS = [
    (0.5, 39.5), (11.0, 39.5), (22.0, 39.5), (29.5, 39.5),
    (0.5, 30.5), (11.0, 30.5),
    (22.0, 25.0), (29.5, 25.0),
    (0.5, 21.0), (11.0, 21.0), (22.0, 21.0), (29.5, 21.0),
    (0.5, 11.0), (15.0, 11.0), (29.5, 11.0),
    (0.5, 0.5), (15.0, 0.5), (29.5, 0.5),
]

# Drop beams under the first floor slab (visible in the parking)
BEAMS = [  # (x0, y0, x1, y1) centre-line
    (0.0, 39.625, 30.0, 39.625), (0.0, 30.5, 11.0, 30.5), (22.0, 25.0, 30.0, 25.0),
    (0.0, 21.0, 30.0, 21.0), (0.0, 11.0, 30.0, 11.0), (0.0, 0.375, 30.0, 0.375),
    (0.375, 0.0, 0.375, 40.0), (11.0, 21.0, 11.0, 40.0), (22.0, 21.0, 22.0, 40.0),
    (15.0, 0.0, 15.0, 21.0), (29.625, 0.0, 29.625, 40.0),
]


# --------------------------------------------------------------------------
# Walls. Each wall is axis-aligned: a centre-line from a to b, thickness t.
# z0/z1 are absolute heights. Openings: (start, end) measured along the
# wall axis in absolute plan coordinates, sill/head measured from `base`.
#   kind: window | jharokha | vent | jaali | door | door_main | door_glass
#         | arch_open | open
#   out : outward normal of an exterior wall (+y, -y, +x, -x) or None
#   swing: side the door leaf opens to (+ / -, along the wall normal axis)
# --------------------------------------------------------------------------
def W(a, b, t, base, top, out=None, openings=(), level="FF", name="wall"):
    return dict(a=a, b=b, t=t, base=base, top=top, out=out,
                openings=[dict(o) for o in openings], level=level, name=name)


def O(s, e, kind, sill=0.0, head=7.0, swing="+"):
    return dict(s=s, e=e, kind=kind, sill=sill, head=head, swing=swing)


FF_TOP = ROOF - SLAB          # underside of roof slab
GF_TOP = FF - SLAB            # underside of first floor slab

WALLS = [
    # ---------------- Ground floor (stilt) ----------------
    # Stair core - full height, entrance faces the road
    W((22.0, 25.375), (22.0, 39.25), EXT_T, GF, GF_TOP, level="GF", name="stair_w"),
    W((21.625, 25.0), (29.25, 25.0), EXT_T, GF, GF_TOP, level="GF", name="stair_s"),
    W((21.625, 39.625), (30.0, 39.625), EXT_T, GF, GF_TOP, out="+y", level="GF",
      name="stair_n", openings=[O(22.75, 25.75, "door_main", 0, 7.5, "-")]),
    W((29.625, 25.375), (29.625, 39.25), EXT_T, GF, GF_TOP, out="+x", level="GF",
      name="stair_e", openings=[O(30.5, 33.5, "jaali", 4.0, 7.0)]),
    # Low screen walls round the parking (4 ft) - neighbours on 3 sides
    W((0.375, 0.75), (0.375, 39.25), EXT_T, GF, GF + 4.0, out="-x", level="GF", name="screen_w"),
    W((0.0, 0.375), (30.0, 0.375), EXT_T, GF, GF + 4.0, out="-y", level="GF", name="screen_s"),
    W((29.625, 0.75), (29.625, 24.625), EXT_T, GF, GF + 4.0, out="+x", level="GF", name="screen_e"),

    # ---------------- First floor ----------------
    # North (road) facade
    W((0.0, 39.625), (30.0, 39.625), EXT_T, FF, FF_TOP, out="+y", name="ff_n", openings=[
        O(3.5, 8.5, "jharokha", 1.5, 7.5),        # Room 1 jharokha
        O(13.5, 15.5, "window", 3.5, 7.0),         # kitchenette
        O(18.0, 21.0, "window", 2.5, 7.5),         # lobby
        O(24.0, 28.0, "jharokha", 1.5, 7.5),       # stair landing jharokha
    ]),
    # West facade
    W((0.375, 0.75), (0.375, 39.25), EXT_T, FF, FF_TOP, out="-x", name="ff_w", openings=[
        O(1.0, 3.25, "jaali", 2.5, 7.0),           # sit-out 2 side jaali
        O(15.5, 17.5, "vent", 5.0, 7.0),           # bath 2
        O(22.0, 24.0, "window", 3.0, 7.0),         # corridor end
        O(31.0, 34.0, "window", 3.0, 7.0),         # room 1 side window
    ]),
    # East facade
    W((29.625, 0.75), (29.625, 39.25), EXT_T, FF, FF_TOP, out="+x", name="ff_e", openings=[
        O(1.0, 3.25, "jaali", 2.5, 7.0),           # sit-out 3 side jaali
        O(15.5, 17.5, "vent", 5.0, 7.0),           # bath 3
        O(22.0, 24.0, "window", 3.0, 7.0),         # corridor end
    ]),
    # Corridor walls
    W((0.75, 25.0), (21.625, 25.0), INT_T, FF, FF_TOP, name="corr_n", openings=[
        O(8.0, 11.0, "door", 0, 7.0, "+"),         # Room 1
        O(17.4, 21.4, "arch_open", 0, 8.0),        # lobby arch
    ]),
    W((0.75, 21.0), (29.25, 21.0), INT_T, FF, FF_TOP, name="corr_s", openings=[
        O(6.5, 9.5, "door", 0, 7.0, "-"),          # Room 2
        O(20.5, 23.5, "door", 0, 7.0, "-"),        # Room 3
    ]),
    # Stair core on first floor
    W((22.0, 25.375), (22.0, 39.25), EXT_T, FF, FF_TOP, name="ff_stair_w",
      openings=[O(36.6, 39.0, "door", 0, 7.0, "-")]),
    W((21.625, 25.0), (29.25, 25.0), EXT_T, FF, FF_TOP, name="ff_stair_s"),
    # Front block partitions
    W((12.0, 25.1875), (12.0, 39.25), INT_T, FF, FF_TOP, name="r1_e",
      openings=[O(27.0, 29.5, "door", 0, 7.0, "+")]),        # bath 1 door
    W((17.0, 25.1875), (17.0, 39.25), INT_T, FF, FF_TOP, name="kit_e",
      openings=[O(34.0, 38.5, "open", 0, 7.0)]),             # kitchenette opening
    W((12.1875, 32.0), (16.8125, 32.0), INT_T, FF, FF_TOP, name="bath1_n"),
    # Back block
    W((15.0, 0.75), (15.0, 20.8125), INT_T, FF, FF_TOP, name="r2_r3"),
    W((0.75, 4.0), (29.25, 4.0), INT_T, FF, FF_TOP, name="sitout", openings=[
        O(2.5, 6.0, "window", 2.5, 7.5),
        O(9.0, 12.0, "door_glass", 0, 7.5, "+"),
        O(18.0, 21.0, "door_glass", 0, 7.5, "+"),
        O(24.0, 27.5, "window", 2.5, 7.5),
    ]),
    W((5.0, 12.8125), (5.0, 20.8125), INT_T, FF, FF_TOP, name="bath2_e",
      openings=[O(14.0, 16.5, "door", 0, 7.0, "-")]),
    W((0.75, 13.0), (4.8125, 13.0), INT_T, FF, FF_TOP, name="bath2_s"),
    W((25.0, 12.8125), (25.0, 20.8125), INT_T, FF, FF_TOP, name="bath3_w",
      openings=[O(14.0, 16.5, "door", 0, 7.0, "+")]),
    W((25.1875, 13.0), (29.25, 13.0), INT_T, FF, FF_TOP, name="bath3_s"),

    # ---------------- Roof ----------------
    W((0.0, 39.625), (21.625, 39.625), EXT_T, ROOF, ROOF + PARAPET_H, out="+y", level="ROOF", name="par_n"),
    W((0.375, 0.75), (0.375, 39.25), EXT_T, ROOF, ROOF + PARAPET_H, out="-x", level="ROOF", name="par_w"),
    W((0.0, 0.375), (30.0, 0.375), EXT_T, ROOF, ROOF + PARAPET_H, out="-y", level="ROOF", name="par_s"),
    W((29.625, 0.75), (29.625, 24.625), EXT_T, ROOF, ROOF + PARAPET_H, out="+x", level="ROOF", name="par_e"),
    # Mumty (stair cabin) - temporary until the next floor is added
    W((22.0, 25.375), (22.0, 39.25), EXT_T, ROOF, ROOF + MUMTY_H, level="ROOF", name="mumty_w",
      out="-x", openings=[O(36.6, 39.0, "door", 0, 7.0, "-")]),
    W((21.625, 25.0), (30.0, 25.0), EXT_T, ROOF, ROOF + MUMTY_H, out="-y", level="ROOF", name="mumty_s",
      openings=[O(25.0, 28.0, "jaali", 3.5, 6.5)]),
    W((21.625, 39.625), (30.0, 39.625), EXT_T, ROOF, ROOF + MUMTY_H, out="+y", level="ROOF", name="mumty_n",
      openings=[O(24.5, 27.5, "jaali", 3.5, 6.5)]),
    W((29.625, 25.375), (29.625, 39.25), EXT_T, ROOF, ROOF + MUMTY_H, out="+x", level="ROOF", name="mumty_e"),
]

# South facade of the first floor is an open arcade (sit-outs)
ARCADE = dict(y=0.375, t=EXT_T, base=FF, top=FF_TOP,
              piers=[0.375, 5.25, 10.125, 15.0, 19.875, 24.75, 29.625],
              spring=6.5, crown=8.25, parapet=3.0)

# Front stilt arches (between the road-side columns)
STILT_ARCHES = [(1.0, 10.5), (11.5, 21.5)]   # clear spans at y = 39.5
STILT_ARCH_SPRING = 6.5                      # above GF

# Roof chhatris (corner kiosks): (x0, y0, size)
CHHATRIS = [(0.25, 34.75, 5.0), (0.25, 0.25, 5.0), (24.75, 0.25, 5.0)]

# --------------------------------------------------------------------------
# Rooms (for labels, areas and floor finishes) - centre-line rectangles
# --------------------------------------------------------------------------
ROOMS = [
    # level, name, (x0, y0, x1, y1), finish
    ("FF", "Room 1", (0.0, 25.0, 12.0, 40.0), "stone"),
    ("FF", "Bath 1", (12.0, 25.0, 17.0, 32.0), "tile"),
    ("FF", "Kitchenette", (12.0, 32.0, 17.0, 40.0), "tile"),
    ("FF", "Lobby", (17.0, 25.0, 22.0, 40.0), "stone"),
    ("FF", "Stair", (22.0, 25.0, 30.0, 40.0), None),
    ("FF", "Corridor", (0.0, 21.0, 30.0, 25.0), "stone"),
    ("FF", "Room 2", (0.0, 4.0, 15.0, 21.0), "stone"),
    ("FF", "Bath 2", (0.0, 13.0, 5.0, 21.0), "tile"),
    ("FF", "Room 3", (15.0, 4.0, 30.0, 21.0), "stone"),
    ("FF", "Bath 3", (25.0, 13.0, 30.0, 21.0), "tile"),
    ("FF", "Sit-out 2", (0.0, 0.0, 15.0, 4.0), "stone"),
    ("FF", "Sit-out 3", (15.0, 0.0, 30.0, 4.0), "stone"),
    ("GF", "Car bay A", (0.5, 24.0, 11.0, 40.0), None),
    ("GF", "Car bay B", (11.0, 24.0, 22.0, 40.0), None),
    ("GF", "Car bay C", (1.0, 2.0, 11.0, 20.0), None),
    ("GF", "Car bay D", (15.5, 2.0, 23.0, 20.0), None),
    ("GF", "Two-wheelers", (23.0, 1.0, 29.5, 20.5), None),
    ("GF", "Stair", (22.0, 25.0, 30.0, 40.0), None),
    ("GF", "Utility / sump", (23.0, 21.0, 29.5, 25.0), None),
]

# Net room areas reported in the docs (sq ft, centre-line, minus bath)
ROOM_SCHEDULE = [
    ("Room 1 (road-facing, jharokha)", "12' x 15'", 180, "Bath 1: 5' x 7'"),
    ("Room 2 (+ private sit-out 15' x 4')", "15' x 17' less bath", 215, "Bath 2: 5' x 8'"),
    ("Room 3 (+ private sit-out 15' x 4')", "15' x 17' less bath", 215, "Bath 3: 5' x 8'"),
    ("Kitchenette", "5' x 8'", 40, "L-counter, sink, small fridge"),
    ("Lobby + corridor", "5' x 15' + 30' x 4'", 195, ""),
    ("Staircase (dog-leg)", "8' x 15'", 120, "continues to future floors"),
]

# --------------------------------------------------------------------------
# Furniture / fittings: (level, kind, (x0, y0, x1, y1), extra)
# --------------------------------------------------------------------------
FURNITURE = [
    # Ground floor - vehicles (car bays are flexible: 2 to 4 cars)
    ("GF", "car", (2.75, 24.5, 8.75, 39.0), dict(color="CarRed")),
    ("GF", "car", (13.5, 24.5, 19.5, 39.0), dict(color="CarWhite")),
    ("GF", "car", (3.0, 4.0, 9.0, 18.5), dict(color="CarBlue")),
    ("GF", "scooter", (23.5, 3.0, 29.0, 5.0), {}),
    ("GF", "scooter", (23.5, 6.5, 29.0, 8.5), {}),
    ("GF", "scooter", (23.5, 10.0, 29.0, 12.0), {}),
    ("GF", "tank", (24.0, 21.6, 26.5, 24.4), {}),     # pump / meter cabinet
    # Room 1
    ("FF", "bed", (0.75, 29.5, 7.25, 34.5), dict(head="-x")),
    ("FF", "side_table", (0.75, 28.0, 2.25, 29.3), {}),
    ("FF", "side_table", (0.75, 34.7, 2.25, 36.0), {}),
    ("FF", "wardrobe", (0.9, 25.25, 5.4, 27.25), {}),
    ("FF", "tv", (11.1, 30.0, 11.8, 34.0), {}),
    ("FF", "armchair", (8.5, 36.0, 10.5, 38.0), {}),
    ("FF", "seat", (3.5, 39.25, 8.5, 41.0), {}),      # jharokha cushion
    # Bath 1
    ("FF", "wc", (14.6, 25.2, 16.8, 26.8), dict(back="+x")),
    ("FF", "basin", (15.2, 28.0, 16.8, 29.6), dict(back="+x")),
    ("FF", "shower", (12.2, 29.9, 16.8, 31.8), {}),
    # Kitchenette
    ("FF", "counter", (12.19, 37.25, 16.81, 39.25), dict(sink=True)),
    ("FF", "counter", (12.19, 32.19, 14.19, 37.25), dict(stove=True)),
    ("FF", "fridge", (15.0, 32.3, 16.7, 33.9), {}),
    # Lobby
    ("FF", "bench", (17.2, 26.0, 18.6, 30.5), {}),
    ("FF", "plant", (20.4, 25.6, 21.5, 26.7), {}),
    # Room 2
    ("FF", "bed", (8.3, 7.0, 14.81, 12.0), dict(head="+x")),
    ("FF", "side_table", (13.3, 5.5, 14.8, 6.8), {}),
    ("FF", "side_table", (13.3, 12.2, 14.8, 13.5), {}),
    ("FF", "wardrobe", (9.8, 18.8, 14.6, 20.8), {}),
    ("FF", "desk", (1.5, 4.2, 5.5, 6.2), {}),
    ("FF", "chair", (2.8, 6.6, 4.2, 8.0), {}),
    ("FF", "tv", (0.75, 8.0, 1.45, 11.5), {}),
    # Bath 2
    ("FF", "wc", (0.8, 17.0, 2.4, 18.6), dict(back="-x")),
    ("FF", "basin", (0.8, 13.4, 2.4, 15.0), dict(back="-x")),
    ("FF", "shower", (0.8, 18.9, 4.8, 20.8), {}),
    # Room 3 (mirror of Room 2)
    ("FF", "bed", (15.19, 7.0, 21.7, 12.0), dict(head="-x")),
    ("FF", "side_table", (15.2, 5.5, 16.7, 6.8), {}),
    ("FF", "side_table", (15.2, 12.2, 16.7, 13.5), {}),
    ("FF", "wardrobe", (15.4, 18.8, 20.2, 20.8), {}),
    ("FF", "desk", (24.5, 4.2, 28.5, 6.2), {}),
    ("FF", "chair", (25.8, 6.6, 27.2, 8.0), {}),
    ("FF", "tv", (28.55, 8.0, 29.25, 11.5), {}),
    # Bath 3
    ("FF", "wc", (27.6, 17.0, 29.2, 18.6), dict(back="+x")),
    ("FF", "basin", (27.6, 13.4, 29.2, 15.0), dict(back="+x")),
    ("FF", "shower", (25.2, 18.9, 29.2, 20.8), {}),
    # Sit-outs
    ("FF", "chair", (3.0, 1.2, 4.5, 2.7), {}),
    ("FF", "chair", (6.0, 1.2, 7.5, 2.7), {}),
    ("FF", "table", (4.7, 1.4, 5.8, 2.5), {}),
    ("FF", "chair", (22.5, 1.2, 24.0, 2.7), {}),
    ("FF", "chair", (25.5, 1.2, 27.0, 2.7), {}),
    ("FF", "table", (24.2, 1.4, 25.3, 2.5), {}),
    # Roof
    ("ROOF", "water_tank", (24.0, 30.0, 28.5, 34.5), {}),
]

# Future-extension provisions (documented + modelled)
EXTENSION_NOTES = [
    "Columns 12\"x12\" and footings sized for G+3; the same column grid repeats on every floor.",
    "Starter bars (capped) left projecting 2 ft above the roof at every column.",
    "Staircase core continues upward; the roof 'mumty' is a light enclosure to be removed when the 2nd floor is built.",
    "Roof slab designed as a floor slab (live load for rooms), so it becomes the 2nd-floor floor without strengthening.",
    "Plumbing stacks (baths 2/3 on the side walls, bath 1 + kitchenette centre) are kept vertical for repeat floors.",
    "Reception planned for the 2nd floor: it sits directly off the stair landing, same as the first-floor lobby.",
]
