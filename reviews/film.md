# Build film review

A separate agent watches the build film frame by frame and says what would confuse a viewer: parts passing through each other or flying the wrong way, the product resting upside down or with its face hidden, flicker, a camera inside a part. It can change the film's direction (how the product rests, where the viewer stands, which way parts back out), and the film is re-rendered and watched again. Automatic checks replay every frame against the 3D models as well.

**Verdict:** pass (round 1). This is a rugged 49 mm smartwatch with an orange sport band, a side crown and action buttons, and a compact internal stack where the display, battery, main PCB, and rear sensor cover fit cleanly together with two internal cable connections.

| Severity | Time | Shot | What a viewer sees | Fix |
|---|---|---|---|---|
| P2 | 17.0 s | glide | As the camera orbits toward the left side during glide, the exploded orange strap band in the foreground briefly crosses in front of the lower PCB and rear cover stack while the Display caption is shown. | No change needed; the highlighted display stack at the top remains unobstructed and the full vertical stack is clearly visible from 8.0s to 15.0s. |
| P2 | 11.0 s | glide | The dark tinted rear sensor window hovering beneath the rear cover has low contrast against the dark studio backdrop until it moves directly under the white rear cover during settle at 29.3s. | No change needed; the sensor window and rear cover cutouts remain legible during settle and reassembly. |

