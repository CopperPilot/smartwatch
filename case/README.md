# Enclosure

`generate_case.py` builds every enclosure part listed in `rea/spec.yaml` (`enclosure.parts`) with
`rea_hardware.cad` (manifold3d) and writes closed STL solids to `case/out/`, in rea's world frame:
X right, Y up, Z out of the board's front face; the board occupies X 0..W, Y -H..0, Z 0..t.
