# Output Shape

Prefer this response shape unless the user asks for something else:

1. Brief restatement
   - One sentence naming the metaphor and overall visual direction.
2. Icon concept summary
   - One short paragraph or two compact bullets describing the dominant object and supporting cue.
3. JSON brief
   - Return a compact fenced `json` block using the schema fields: `app_concept`, `primary_metaphor`, `supporting_motifs`, and `composition_family`.
4. SVG
   - Return a single fenced `svg` block.
5. Rationale
   - One short paragraph or a few compact bullets covering:
     - metaphor choice
     - material / depth treatment
     - palette logic
     - silhouette and small-size readability
6. Validation note
   - Include a compact note covering small-size readability and the PARC pass.
   - Mention any PARC issue that shaped the final design.
7. Optional refinement notes
   - Include only when the concept has a clear tradeoff or when the user requested alternates.

## Defaults

- Return one JSON brief and one SVG by default.
- Keep the JSON concise and artifact-oriented rather than verbose.
- Only include alternates on explicit request or when the first concept is visibly underdetermined.
