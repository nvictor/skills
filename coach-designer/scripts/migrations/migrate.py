#!/usr/bin/env python3
"""Prepare/apply a conversational-coaching update across local skills and design repos.

Default is a dry run. --apply writes files, never commits or deploys.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PRINCIPLES = '''## Teaching approach

Teach progressively, adapting to the learner's goals, prior knowledge, and demonstrated understanding.

- Introduce concepts in a sensible prerequisite order.
- Explain clearly, with examples when useful.
- Check understanding before advancing to material that depends on it. Use questions, applications, teach-backs, or observed work as appropriate.
- Adapt explanations and practice when the learner struggles. Do not mistake a correct guess for durable mastery.
- Favor deliberate practice, evidence-based feedback, and opportunities to improve.
- Increase difficulty when performance supports it.
- Keep the conversation natural. Do not require fixed sentence counts, a checking question after every explanation, or a separate readiness confirmation after every successful assessment.
- Respect requests to pause, slow down, practice more, or revisit a concept.

Use judgment to decide when to explain, assess, practice, or continue. Avoid unnecessary confirmation questions and artificial transitions. Keep each session within its limits; preserve unfinished work for resumption.
'''


def replace_section(text, start, end, replacement):
    pattern = re.compile(r'(?ms)^' + re.escape(start) + r'\n.*?(?=^' + re.escape(end) + r'\n)')
    result, n = pattern.subn(lambda _: replacement.rstrip() + '\n\n', text, count=1)
    if n != 1:
        raise ValueError(f'Cannot locate section {start} through {end}')
    return result


def update_skill(text):
    text = text.replace('name: coach-designer\n', 'name: coach-designer\nmetadata:\n  version: "2.0.0"\n', 1) if 'metadata:\n  version:' not in text else re.sub(r'(metadata:\n  version: )[^\n]+', r'\g<1>"2.0.0"', text, count=1)
    text = replace_section(text, '### 3. Design the learning system', '### 4. Define progression, feedback, and continuity', '''### 3. Design the learning system

Define an observable long-term outcome, such as what the learner should be able to do after approximately 100 sessions, and the fewest competencies needed to reach it. Design meaningful practice, feedback, assessment, and progression around that outcome. Use deliberate practice, simulations, projects, critique and revision, retrieval, reflection, or teaching back as appropriate. Wait for a meaningful practice attempt before supplying its solution, while teaching missing prerequisites when needed.

''' + PRINCIPLES + '''
Choose guided explanation for unfamiliar material and practice for previously learned material or explicit practice requests. Collect necessary setup facts without treating them as tests. Let the agent adapt the teaching sequence instead of imposing a fixed conversational protocol.
''')
    text = re.sub(r'Record the mode, current concept and objective, phase, outstanding question, evidence of understanding, unresolved misconception, next concept, readiness status, and any exhausted session budget\.', 'Record the current objective, interaction position, outstanding work, observed evidence, and any exhausted session budget.', text)
    text = text.replace('Resume the recorded phase without automatically reteaching or restarting.', 'Resume unfinished work naturally without automatically reteaching or restarting.')
    text = text.replace('## Teaching approach', '#### Teaching approach', 1)
    if LEGACY not in text:
        text = text.replace('### 4. Define progression, feedback, and continuity', LEGACY + '\n\n### 4. Define progression, feedback, and continuity')
    return text


def update_rubric(text):
    text = replace_section(text, '## Session design', '## Feedback', '''## Session design

- Keep sessions within their requested duration and choose one useful objective from evidence.
- Explain and assess progressively, checking understanding before advancing to dependent material.
- Use questions, applications, teach-backs, or observed work to assess understanding naturally.
- Adapt to confusion, learner requests, and demonstrated performance without a fixed conversational script.
- Do not require a separate readiness confirmation after a successful assessment.
- Give focused feedback and opportunities to apply it within the remaining session budget.
- Pause incomplete work at session limits and preserve its position for resumption.
''')
    text = re.sub(r'- Preserve mode, concept and objective, phase, outstanding question, understanding evidence, unresolved misconception, next concept, readiness status, and exhausted budget in an open interaction\.', '- Preserve the current objective, interaction position, outstanding work, observed evidence, and remaining session budget in an open interaction.', text)
    text = text.replace('- mode-specific loops and starting instructions preserve the separate understanding and readiness gates', '- assessment precedes dependent material without unnecessary readiness gates')
    return text


def update_format(text):
    text = text.replace('recording mode, concept/objective, phase, outstanding question, understanding evidence, unresolved misconception, next concept, readiness, and exhausted budget when the interaction is incomplete', 'recording the current objective, interaction position, outstanding work, observed evidence, and remaining budget when an interaction is incomplete')
    text = text.replace('- teach one prerequisite-ordered concept and ask one checking question; repair gaps on the same concept\n- after demonstrated understanding, ask a separate readiness question and wait for an explicit affirmative reply before new material or a new practice activity\n- preserve these gates in every mode and starting instruction; pedagogical readiness grants no authority for external actions', '- introduce concepts in prerequisite order and assess understanding before dependent material\n- adapt teaching and practice to observed performance without fixed question counts or mandatory readiness confirmations\n- respect learner requests to pause or revisit material; pedagogical progress grants no authority for external actions')
    text = text.replace('mode, concept/objective, phase, outstanding question, understanding evidence, misconception, next concept, readiness, and exhausted budget', 'objective, interaction position, outstanding work, observed evidence, and remaining budget')
    text = text.replace('Useful phases are `teaching`, `awaiting_check`, `remediation`, `awaiting_readiness`, and `practice`.', 'Legacy phases such as `awaiting_readiness` remain valid; resume them naturally without imposing that gate on future concepts.')
    text = text.replace('Resume an outstanding check, repair, readiness question, or practice attempt without automatically restarting instruction.', 'Resume outstanding checks, repairs, or practice attempts without automatically restarting instruction. If legacy state records `awaiting_readiness`, honor any learner request to pause, otherwise continue naturally after acknowledging demonstrated understanding.')
    if LEGACY not in text:
        text = text.replace('## `state.md`', LEGACY + '\n\n## `state.md`', 1)
    return text


def update_template(text):
    if '## Mode selection and starting behavior' not in text and '## Teaching approach' in text:
        return text
    text = replace_section(text, '## Mode selection and starting behavior', '## Session limits and continuity', '''## Teaching approach

Resume unfinished work naturally. Otherwise choose an objective based on learner goals and observed progress. Explain unfamiliar prerequisites and use realistic practice when appropriate. Collect setup facts without grading them as understanding.

''' + PRINCIPLES.replace('## Teaching approach\n\n', '') + '''
## Practice and progression

Use realistic challenges, specific evidence-based feedback, retries, and spaced review. Let the learner attempt a challenge before supplying its solution, while freely teaching missing prerequisites.

{{Specify meaningful practice modes, mastery evidence, difficulty dimensions, and spaced review.}}
''')
    text = text.replace('For an open interaction retain mode, concept/objective, phase, outstanding question, understanding evidence, unresolved misconception, next concept, readiness status, and exhausted budget. Resume that phase without automatically reteaching;', 'For an open interaction retain the current objective, interaction position, outstanding work, observed evidence, and remaining budget. Resume naturally without automatically reteaching;')
    if LEGACY not in text:
        text += '\n' + LEGACY + '\n'
    return text


LEGACY = """Legacy interaction phases remain valid. Resume pending checks, remediation, or practice from recorded evidence without restarting. For `awaiting_readiness`, honor a pause or revisit request; otherwise acknowledge demonstrated understanding and continue naturally within the session budget. Unknown understanding remains unknown and must be assessed before dependent material. Preserve existing state fields and useful history; no state conversion is required."""


def update_runner(text):
    old = 'pending check, remediation, readiness question, or practice attempt.'
    text = text.replace(old, 'pending check, remediation, or practice attempt. For legacy `awaiting_readiness`, honor pause or revisit requests; otherwise acknowledge demonstrated understanding and continue naturally within the session budget.')
    return text


def update_coach_prompt(text):
    # Replace complete, known generic teaching blocks, never whole domain-bearing lines.
    text = re.sub(r'(?ms)^## Learning sequence\n.*?(?=^## Budget and progression\n)',
                  lambda _: PRINCIPLES + '\n' + LEGACY + '\n\n', text)
    text = re.sub(r'(?ms)^# Learning mode and teaching gates\n.*?(?=^# Bounded session loop\n)',
                  lambda _: PRINCIPLES.replace('## Teaching approach', '# Teaching approach', 1) + '\n' + LEGACY + '\n\n', text)
    text = re.sub(r'(?ms)^## Guided learning\n.*?(?=^## Practice\n)',
                  lambda _: PRINCIPLES + '\n' + LEGACY + '\n\n', text)
    replacements = {
        'After guided learning and readiness, or evidence-supported retrieval': 'After guided learning with demonstrated understanding, or evidence-supported retrieval',
        'check understanding, and wait for readiness before application or criticism': 'assess understanding before application or criticism',
        'application prompts all count': 'application prompts, count',
        'After readiness, invite': 'After assessing understanding, invite',
        'Checks, readiness questions, setup questions, and application prompts': 'All learner-facing prompts, including checks, setup questions, and application prompts',
        'require separate readiness before role-play': 'assess understanding before role-play',
        'with a check and readiness': 'with an appropriate understanding assessment',
        'through separate understanding and readiness exchanges': 'after evidence of understanding',
        'then after readiness invite': 'then when understanding is demonstrated invite',
        'after readiness, apply': 'after assessing understanding, apply',
        'through its own check and readiness exchange': 'with an appropriate assessment before dependent material',
        'guided-learning gates': 'teaching guarantees',
        'understanding and readiness permit practice': 'demonstrated understanding supports practice',
        'teaching gates and session limits': 'teaching guarantees and session limits',
        'Follow the corresponding loop and gates above.': 'Apply the teaching guarantees above.',
        'or follow the guided-learning check and separate readiness gates': 'or assess understanding before dependent material',
        'After a successful guided check, ask a separate readiness question and wait before advancing.': 'Advance to dependent material only when understanding is demonstrated; adapt the next activity to the evidence.',
        'After a correct check, ask only the separate readiness question and wait.': 'After assessing understanding, adapt the next step to the evidence and remaining session budget.',
        'Count checking, readiness, practice, and retry prompts.': 'Count all learner-facing prompts, including checks, practice, and retries.',
        'without adding a final check or readiness question': 'without adding a question beyond the budget',
        'record its evidence and defer readiness': 'record its evidence and defer further work',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if 'Teaching approach' not in text:
        text = text.rstrip() + '\n\n' + PRINCIPLES + '\n' + LEGACY + '\n'
    return text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--skills', type=Path, required=True)
    p.add_argument('--design', type=Path, required=True)
    p.add_argument('--apply', action='store_true', help='Write changes. No commits or deployments.')
    a = p.parse_args()
    root = a.skills / 'coach-designer'
    edits = {
        root / 'SKILL.md': update_skill,
        root / 'references/quality-rubric.md': update_rubric,
        root / 'references/package-format.md': update_format,
        root / 'assets/coach-package/prompt.md': update_template,
        root / 'assets/coach-package/runner.md': update_runner,
    }
    coaches = a.design / 'agents/coaches'
    changed_coaches = []
    packages = []
    for manifest in sorted(coaches.glob('*/manifest.json')):
        packages.append(manifest.parent)
        data = json.loads(manifest.read_text())
        prompt = manifest.parent / data['prompt_file']
        runner = manifest.parent / data['runner_file']
        runner_original = runner.read_text()
        runner_revised = update_runner(runner_original)
        if runner_revised != runner_original:
            edits[runner] = lambda _old, revised=runner_revised: revised
        original = prompt.read_text()
        revised = update_coach_prompt(original)
        if revised != original:
            edits[prompt] = lambda _old, revised=revised: revised
            changed_coaches.append(manifest)
    for manifest in changed_coaches:
        def bump(original):
            data = json.loads(original)
            data['version'] = data['version'] + 1
            return json.dumps(data, indent=2, ensure_ascii=False) + '\n'
        edits[manifest] = bump
    # Plan everything before writing. Validate the complete proposed packages in isolation.
    proposed = {}
    originals = {}
    for path, transform in edits.items():
        original = path.read_text()
        revised = transform(original)
        if revised != original:
            proposed[path] = revised
            originals[path] = original
    validator = root / 'scripts/validate_coach_package.py'
    with tempfile.TemporaryDirectory(prefix='coach-behavior-') as temp:
        for package in packages:
            staged = Path(temp) / package.name
            shutil.copytree(package, staged)
            for path, revised in proposed.items():
                if path.is_relative_to(package):
                    (staged / path.relative_to(package)).write_text(revised)
            result = subprocess.run([sys.executable, str(validator), str(staged)], capture_output=True, text=True)
            print(result.stdout, end='')
            if result.returncode:
                raise ValueError(f'Validation failed for {package}: {result.stderr}')
    for path in proposed:
        if path.read_text() != originals[path]:
            raise ValueError(f'File changed during planning: {path}')
    for path, revised in proposed.items():
        print(('WRITE' if a.apply else 'WOULD UPDATE'), path)
        if a.apply:
            path.write_text(revised)
    print(f'{len(changed_coaches)} coach manifests incremented in the plan; {len(packages)} packages validated; no state, schedule, schema, or deployment settings changed')


if __name__ == '__main__':
    main()
