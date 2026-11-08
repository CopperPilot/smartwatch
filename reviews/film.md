# Build film review

A separate agent watches the build film frame by frame and says what would confuse a viewer: parts passing through each other or flying the wrong way, the product resting upside down or with its face hidden, flicker, a camera inside a part. It can change the film's direction (how the product rests, where the viewer stands, which way parts back out), and the film is re-rendered and watched again. Automatic checks replay every frame against the 3D models as well.

**Verdict:** pass (round 1). This is a rugged 49 mm smartwatch with a front IPS display under flat cover glass, side rotary crown and buttons, an internal ESP32-S3 main board and LiPo battery, a domed rear heart-rate sensor cover, and a slide-in sport band that all assemble cleanly.

| Severity | Time | Shot | What a viewer sees | Fix |
|---|---|---|---|---|
| P2 | 14.0 s | glide | The small circular rear optical sensor_window at the bottom of the exploded stack is mostly tucked beneath the domed rear_cover from the upper camera elevation, only peeking out briefly during glide and settle. | No change needed; the main assembly layers, display stack, PCBA, battery, side actuators, rear cover, and strap band all read clearly without changing camera elevation. |

