# Output Shape

Prefer this response shape unless the user asks for something else:

1. Brief restatement
   - One sentence naming the metaphor and overall visual direction.
2. Icon concept summary
   - One short paragraph or two compact bullets describing the dominant object and supporting cue.
3. SVG
   - Return a single fenced `svg` block.
4. Rationale
   - One short paragraph or a few compact bullets covering:
     - metaphor choice
     - material / depth treatment
     - palette logic
     - silhouette and small-size readability
5. Optional refinement notes
   - Include only when the concept has a clear tradeoff or when the user requested alternates.

## Defaults

- Return one SVG by default.
- Do not force JSON into the user-facing answer.
- Only include alternates on explicit request or when the first concept is visibly underdetermined.
