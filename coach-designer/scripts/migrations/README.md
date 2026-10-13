# Coaching behavior update

`migrate.py` is a one-time update for the existing portable coaches in
`design/agents/coaches`. It replaces the legacy teaching protocol with progressive
learning, assessment before advancing, adaptation, and continuity. It preserves
the package architecture and manifest schema.

Use Python 3.9 or later. The script uses only the standard library. Copy or sync
this skill, including its validator, to the other computer before running it.
Adjust the repository paths below if they differ on that computer.

## Run

1. Preview the changes and validate the proposed coach packages without writing:

   ```bash
   python3 ~/Developer/skills/coach-designer/scripts/migrations/migrate.py \
     --skills ~/Developer/skills \
     --design ~/Developer/design
   ```

2. Apply the changes locally:

   ```bash
   python3 ~/Developer/skills/coach-designer/scripts/migrations/migrate.py \
     --skills ~/Developer/skills \
     --design ~/Developer/design \
     --apply
   ```

3. Review the resulting diffs before committing or deploying:

   ```bash
   git -C ~/Developer/skills diff
   git -C ~/Developer/design diff
   ```

## Scope and checks

- Updates the skill instructions, quality rubric, behavioral guidance in the
  package reference, prompt template, and runner template.
- Updates coach prompts and applicable runners. Sets the skill version to `2.0.0`
  and increments each changed coach prompt's manifest version by one.
- Leaves state files, progress, schedules, deployment settings, and migration
  records untouched. Legacy interaction phases remain supported.
- Validates every discovered package in a temporary copy before writing any
  planned changes. Validation errors stop the update. Warnings need review.
- Makes no commits, pull requests, or live deployment changes.
- Repeating it against the same updated inputs produces no further changes.

The transformations recognize specific legacy headings and wording. This is a
historical migration, not a general coach refactoring tool. Review prompt diffs
for preserved subject goals and contradictory legacy instructions even when
validation passes. If required skill sections cannot be found, the script stops;
inspect the target skill rather than forcing the update. Do not run it against a
newer skill version without reviewing its changes, since it sets version `2.0.0`.

Deployment is a separate operation. Validate each changed package again after
any manual edits and before deployment, using its actual directory:

```bash
python3 ~/Developer/skills/coach-designer/scripts/validate_coach_package.py \
  ~/Developer/design/agents/coaches/sre-coach
```
