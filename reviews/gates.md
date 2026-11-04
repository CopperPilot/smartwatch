# Design gates

Deterministic checks run on the design files (KiCad, the enclosure meshes, the assembly and the manufacturing outputs). Each one is a pytest case in CopperPilot's build pipeline.

Verdict **PASS**: 46 pass, 2 warn, 0 fail, 0 error, 0 not applicable. Generated 2026-11-04T03:15:48Z.

| Gate | What it checks | Status | Notes |
|---|---|---|---|
| `spec.valid` | Scope contract rea/spec.yaml is complete and consistent | PASS |  |
| `inputs.present` | Input images and prompt are inside the workspace | PASS |  |
| `brand.clean` | No third-party brand marks in names, silkscreen, case or docs | PASS |  |
| `scope.board_fits` | Every board fits inside the product's rounded outline, inside its wall | PASS |  |
| `sourcing.bom` | Every placed part has a live, in-stock part at the fab's parts source | WARN | 32 extended parts (each adds a JLCPCB feeder fee); prefer basic parts where equivalent |
| `kicad.erc` | Schematic ERC: 0 errors | PASS |  |
| `kicad.drc` | PCB DRC with schematic parity + zone refill: 0/0/0 | WARN | DRC warning silk_over_copper x23<br>DRC warning lib_footprint_mismatch x7 |
| `kicad.rules` | Project rules are no looser than the fab profile; nothing silenced | PASS |  |
| `board.contract` | Board outline, holes and user-facing parts match the spec | PASS |  |
| `kicad.models` | Every placed footprint has a 3D model on disk | PASS |  |
| `kicad.refs` | Modules with a verified reference symbol use it (no hand-drawn pinouts) | PASS |  |
| `board.antenna` | A module's printed antenna sits at the board edge with nothing around it | PASS |  |
| `kicad.parts` | Every part sits on the footprint of that exact LCSC part, with its real 3D model (no placeholders) | PASS |  |
| `board.cable_pinout` | Both ends of each board-to-board cable carry the same signal on each wire | PASS |  |
| `board.stackup` | The board's layer count, thickness and stackup match the spec and the fab | PASS |  |
| `board.high_speed` | Declared high-speed groups (DDR, MIPI, USB) are routed, length-matched and on target impedance | PASS |  |
| `board.user_ports` | Every receptacle a person plugs into sits behind a case opening | PASS |  |
| `board.cc_protection` | USB-C CC lines are not clamped to VBUS by a rail-referenced ESD array | PASS |  |
| `board.ground_pins` | No ground pin is left unconnected | PASS |  |
| `board.pd_autonomous` | A USB-PD charging input negotiates with no processor running | PASS |  |
| `board.connector_mating` | Every connector mates from a known side, toward its cable, with a clear mating zone in its footprint | PASS |  |
| `board.height_zones` | Parts under an overhead part stay below the zone's height limit | PASS |  |
| `board.port_facing` | Every user-facing port's connector opens towards its case opening (3D model) | PASS |  |
| `review.design` | Datasheet-level design review (CopperPilot validate): no open P0 or P1 findings | PASS |  |
| `mech.meshes` | Enclosure parts exist, are closed solids, and fit the envelope | PASS |  |
| `mech.openings` | Every front/rear/edge feature has an opening in the shell, at its size | PASS |  |
| `mech.assembly` | Draft assembly: no collisions seated or along insertion paths | PASS |  |
| `mech.dfm` | Each enclosure part is manufacturable by its process (walls, build size) | PASS |  |
| `fidelity.dims` | Key proportions (bezel, edge and centre thickness, overall size) match the reference | PASS |  |
| `integration.assembly` | Final assembly with the KiCad-exported PCBA: no collisions | PASS |  |
| `integration.cables` | Every cable joins two real connectors and fits its route in every pose | PASS |  |
| `integration.actuators` | Every button, crown, dial or sensor window physically works its part | PASS |  |
| `integration.ports` | Every port opening has its connector right behind it (a plug can mate) | PASS |  |
| `integration.mating` | Every connector faces what mates with it, and every mounting hole sits on a boss (checked on the 3D models) | PASS |  |
| `integration.band` | A wrist band closes round the wrist, its sensor faces the wrist, and a slide-on charger meets its contacts | PASS |  |
| `integration.retention` | Every assembled part is held in place by something real (snap, clip, screw, adhesive, press fit, captured) | PASS |  |
| `integration.rf` | A radio's antenna is not sealed inside metal (an RF window exists) | PASS |  |
| `integration.battery_fill` | In a laptop- or tablet-sized product the battery fills the free space at its height | PASS |  |
| `integration.camera_view` | Every camera sees out: its whole field of view clears the case | PASS |  |
| `fab.package` | Gerbers, drill, BOM and CPL exist and agree with the PCB | PASS |  |
| `video.build` | 3D build video exists and actually shows motion | PASS |  |
| `tests.integrity` | Generated test suite is the rea template, unmodified | PASS |  |
| `fidelity.judge` | Independent visual judge: renders match the reference photos | PASS |  |
| `spec.locked` | Scope contract unchanged since scope (or changes justified) | PASS |  |
| `system.valid` | System spec: modules, interfaces, power tree, assembly order are consistent | PASS |  |
| `system.modules` | Every built module passes all of its own gates | PASS |  |
| `system.assembly` | Modules do not collide with each other, seated or along system insertion paths | PASS |  |
| `system.cables` | Every inter-module cable plugs into a real port on each module and is long enough | PASS |  |
