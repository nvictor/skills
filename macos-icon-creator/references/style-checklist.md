# Raster Review

## Render the deliverable

Render the final SVG and inspect the actual raster output at 16, 32, 64, and 128 px, plus a larger view for join and material defects. View small samples at their intended display size; zooming alone conceals readability problems. Check transparency and edge contrast against light and dark backgrounds.

Use a renderer available in the environment and record which one was used. A browser preview can support design review, but it does not establish fidelity in a different export pipeline. When a destination or export tool is known, inspect its output too. If that path is unavailable, identify it as unverified.

In the Dashi integration, AppKit's `NSImage` SVG rendering omitted filter shadows. Treat this as a demonstrated compatibility risk, not a claim that all Apple renderers behave alike. Check filters, clipping, masks, gradients, transparency, and bounds in the actual destination. If effects disappear, use supported vector shading or a verified raster export when appropriate to the requested deliverable.

Quick Look can provide a convenient macOS preview, for example:

```bash
qlmanage -t -s 512 -o /tmp /absolute/path/icon.svg
```

Its thumbnail is not proof of another renderer's output. Inspect the generated image's canvas and background before using it for small-size comparisons. Distinguish a downsampled large render from output rendered directly at a target size when evaluating an export pipeline.

## Inspect and revise

- At 16 px: does the dominant silhouette and value structure survive?
- At 32 px: is the primary object recognizable, with essential supporting cues distinct?
- At 64 and 128 px: does depth read clearly without muddiness or distracting detail?
- At larger sizes: are joins smooth, overlaps intentional, and effects free of clipping or unwanted seams?

Use PARC to diagnose composition problems:

- **Proximity:** related pieces read as a group; separation and contact make sense.
- **Alignment:** axes, curves, and edge relationships look deliberate.
- **Repetition:** lighting and material behavior follow a coherent logic.
- **Contrast:** the main object dominates; secondary cues remain subordinate.

After a correction, rerender the affected output. Report only meaningful findings and any unresolved limitation; do not claim readability from SVG source inspection alone.
