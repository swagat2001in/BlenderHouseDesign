# Home-cum-Hotel on a 1200 sq ft plot: design and tooling plan

Status: **phases 1-4 built** (see "Decisions" below). The original draft is kept underneath for reference.

## Decisions (from review)

| Question | Answer |
|---|---|
| Plot | 30' x 40', road on the **north** |
| Authority | Puri. No approval needed (self-financed), but the design still keeps to normal good practice |
| Parking | Flexible: 2 cars at the front + 2 tandem behind (optional), 4-6 two-wheelers |
| Vertical access | Staircase only (dog-leg), no lift |
| Reception | Not now. It goes on the future 2nd floor, off the stair landing |
| Future floors | Columns/footings for G+3, starter bars, stair continues, roof slab = future floor |
| Tooling | Everything runs headless in the cloud: Blender `bpy` -> renders + `.glb` + web viewer |
| Style | Traditional Rajasthani haveli (Jaipur pink, jharokhas, chhatris, jaali, cusped arches) |

## As built (differences from the draft below)

- Stair moved to the **north-east corner** (8' x 15'), entered straight from the road, so cars do not cross the stair.
- First floor: Room 1 (12' x 15') faces the road with a jharokha. Rooms 2 and 3 (15' x 17' each, less the bath) are at the back with private 4'-deep arcaded sit-outs. Baths 2 and 3 sit on the side walls for natural ventilation.
- Kitchenette 5' x 8' with a window on the road side; Bath 1 next to it needs an exhaust duct.
- Levels: plinth +1'-0", first floor +11'-6", roof +22'-0" (10'-6" floor to floor).

## 1. Brief

| Item | Requirement |
|---|---|
| Plot | 1200 sq ft (assumed **30 ft x 40 ft**, about 9.14 m x 12.19 m) |
| Ground floor | Stilt parking only, plus the staircase core |
| First floor | 3 guest rooms, each with an attached bathroom, and 1 small kitchenette |
| Use | Residential home that also works as a small hotel or guest house |

## 2. Draft space program (first floor, about 1200 sq ft gross)

| Space | Size (ft) | Area (sq ft) |
|---|---|---|
| Room 1 + attached bath | 12x13 + 5x8 | 196 |
| Room 2 + attached bath | 12x13 + 5x8 | 196 |
| Room 3 + attached bath | 12x13 + 5x8 | 196 |
| Kitchenette (pantry for guests or caretaker) | 6x8 | 48 |
| Staircase (dog-leg, continues to terrace) | 8x14 | 112 |
| Corridor and lobby | about 4 ft wide | about 300 |
| Walls (about 10%) | | about 120 |

Concept layout (plan view, road at the bottom):

```
+--------------------------------------+  40'
|  ROOM 3        | BATH3 |  ROOM 2     |
|  12'x13'       | 5'x8' |  12'x13'    |
|----------------+-------+------+------|
|      CORRIDOR / LOBBY (4' wide)      |
|------+---------+--------------+------|
| STAIR | KITCH  |  ROOM 1      |BATH2 |
| 8x14  | 6x8    |  12'x13'     |BATH1 |
+--------------------------------------+  0'
0'                                    30'
```

Ground floor: the same footprint on columns, with 3 car bays (about 8.5 ft x 16.5 ft each) or 2 cars plus bikes, a driveway from the road side, and the stair core plus an optional water tank or meter room.

Structure: RCC frame with about 9"x12" columns on a grid of about 10-12 ft. Floor-to-floor height is about 10 ft, with a stilt clear height of at least 7.5-8 ft.

> This is a concept. Setbacks, FAR and stilt-parking rules depend on the local authority and can cut the buildable footprint well below 1200 sq ft. A licensed architect or engineer must check the design before construction.

## 3. Tooling: how Claude produces the 3D design

**Recommended: Blender + a parametric Python generator + Blender MCP**

```
design/spec.yaml        <- single source of truth (plot, rooms, walls, doors, windows)
        |
generator/build.py      <- Blender Python (bpy) script: spec -> 3D model
        |
   +----+-------------------------+-----------------------------+
   | headless (this cloud repo)   | interactive (your PC)       |
   | blender -b -P build.py       | Blender + blender-mcp addon |
   | -> .blend, .glb, PNG renders | Claude drives Blender live  |
   +------------------------------+-----------------------------+
        |
viewer/index.html       <- three.js web viewer of the .glb (orbit, floor toggle)
```

Why:
1. **Blender MCP** (open-source `blender-mcp` addon and MCP server) lets Claude Desktop or Claude Code on your machine create and modify objects in a running Blender. It works well for live, iterative "move this wall" sessions.
2. **Parametric script + spec file**: the design lives as text in git, so it is reproducible and diffable. Changing a room size means editing one line and rebuilding. It also runs headless in this cloud session, which cannot reach a Blender window on your computer.
3. **Exports**: `.blend` for editing, `.glb` for the web viewer, PNG renders (isometric, per-floor cutaway, top-down plan), and optionally IFC through Bonsai (formerly BlenderBIM) for BIM and architect handoff.

Alternatives considered: SketchUp MCP (easier for architects, but paid), FreeCAD MCP (CAD-precise, but weaker visuals), and a three.js-only model (no proper editing tool).

## 4. Implementation phases

| Phase | Deliverable |
|---|---|
| 0 | Confirm the open questions below |
| 1 | `spec.yaml` + 2D floor-plan SVGs (ground and first floor) with dimensions, for layout sign-off |
| 2 | `build.py`: slab, columns, walls with door and window openings, stairs, parapet, car-bay markings |
| 3 | Materials, basic furniture (bed, wardrobe, WC, kitchen counter, cars), lighting, renders |
| 4 | `.glb` export + web viewer (orbit, hide or show floors, room labels) |
| 5 | Setup guide for Blender MCP on your machine (Claude Desktop or Claude Code config) |
| 6 | Optional: IFC export, area schedule, rough bill of quantities |

## 5. Open questions for you

1. Plot dimensions and orientation: 30x40, 40x30, or other? Which side faces the road, and which way is north?
2. City or authority, so the design can respect setbacks and stilt-parking rules.
3. Parking need: number of cars and bikes?
4. Stairs only, or a small lift as well?
5. Should the kitchenette serve guests, the owner, or a caretaker? Is a small reception or owner's room needed?
6. Future floors or a terrace (rooftop sit-out, solar, water tank)?
7. Will you run Blender locally (for the live MCP workflow), or should everything run headless here with renders and a web viewer?
8. Style preferences: modern flat roof, materials, colours?
