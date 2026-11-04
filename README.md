# Puri Haveli Home-Hotel

Concept design for a home-cum-guesthouse on a **30' x 40' (1,200 sq ft) plot in Puri**, with the road on the north side.

- **Ground floor:** open stilt parking for 2 to 4 cars and 4 to 6 two-wheelers, plus a dog-leg stair entered directly from the road.
- **First floor:** three guest rooms with attached baths and a 5' x 8' kitchenette. Rooms 2 and 3 have private arcaded sit-outs.
- **Styles:** four skins over the same plan:
  - **Rajasthani haveli**: Jaipur-pink lime plaster with cream outlines, jharokhas, chhajja eaves, cusped arches, jaali screens, a kangura parapet and domed chhatris (`output/`).
  - **Odia / Kalinga**: laterite walls with khondalite bands, corbelled stone openings, temple-style stone balusters, bay windows and roof pavilions with stepped *pidha* roofs, a *rekha* tower over the stair, a Konark-wheel relief and a Pattachitra mural (`output/odia/`).
  - **Chettinad (Tamil Nadu)**: egg-white lime plaster with red-oxide bands, granite pillars with teak bracket capitals, peacock-green louvred shutters under stained-glass transoms, carved teak balconies under Mangalore-tile canopies, a teak colonnade at the sit-outs, a stucco crest and a tiled terrace pavilion with an oonjal swing; Athangudi-tile floors (`output/chettinad/`).
  - **Kerala (nalukettu-inspired)**: a steep hip-and-gable clay-tile roof over the terrace on timber posts (removable for the next floor) with lattice mukhappu gables and brass kodi finials, white lime walls with laterite courses, azhi bar windows, gabled balconies with charupady seats, red-oxide floors and wooden ceilings (`output/kerala/`).
- **Future floors:** the column grid, footings, stair and roof slab are planned for G+3. Capped starter bars are left above the roof. The reception goes on the 2nd floor later.

The whole design is generated from code. **Blender** (headless, as the `bpy` Python module) builds the 3D model from one layout file, renders it with Cycles, and exports `.blend` and `.glb` files. A small script draws the dimensioned plans from the same file.

```
design/layout.py          single source of truth: plot, levels, walls, openings, rooms, furniture (feet)
generator/build_model.py  Blender builder (Rajasthani): walls, arches, jharokhas, chhatris, stair, furniture ...
generator/style_odia.py   Odia / Kalinga skin (subclass of the builder)
generator/style_chettinad.py  Chettinad skin (subclass of the builder)
generator/style_kerala.py Kerala skin (subclass of the builder)
generator/render.py       renders the views + exports output/model/home_hotel.{blend,glb}
generator/plans.py        dimensioned SVG floor plans
output/index.html         web page: live 3D viewer (three.js) + renders + plans
output/renders/*.jpg      Cycles renders
output/plans/*.svg        ground floor, first floor, roof plans
output/odia/              same renders + model in the Odia / Kalinga style
output/chettinad/         same renders + model in the Chettinad style
output/kerala/            same renders + model in the Kerala style
output/model/             home_hotel.blend (saved with Blender 5.2), home_hotel.glb (any 3D viewer), home_hotel.gltf.json (same model, used by the web page)
docs/PLAN.md              the brief, decisions and phases
```

## Rebuild after changing the design

```bash
pip install bpy                     # Blender 5.x as a Python module (needs Python 3.13)
python generator/render.py          # all views at full quality + .blend/.glb  (~10 min on 4 CPU cores)
python generator/render.py --style odia        # Odia / Kalinga version -> output/odia/
python generator/render.py --style chettinad   # Chettinad version -> output/chettinad/
python generator/render.py --style kerala      # Kerala version -> output/kerala/
python generator/render.py --views hero --samples 32 --scale 50 --no-export   # quick preview
python generator/plans.py           # SVG plans (plain Python, no Blender needed)
```

To view the web page locally, serve the `output/` folder (browsers block loading the `.glb` from `file://`):

```bash
cd output && python -m http.server 8000     # then open http://localhost:8000
```

## Optional: drive Blender live with Claude (MCP)

On a computer with Blender installed, the open-source `blender-mcp` add-on and server let Claude Desktop or Claude Code edit a running Blender scene. Open `output/model/home_hotel.blend`, start the add-on, and ask for changes interactively. For changes you want to keep, edit `design/layout.py` instead and rebuild, so the model, renders and plans stay in sync.

## Before construction

This is a concept model. It is not a construction drawing. Before construction:

- Have a structural engineer design the frame and foundations for G+3. Puri is coastal and in a cyclone zone.
- Check the jharokha and eave projections. About 1'-9" projects past the north line.
- Plan exhaust ventilation for Bath 1, which has no outside wall.
