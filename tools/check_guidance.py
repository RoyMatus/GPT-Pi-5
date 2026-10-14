"""Validate project skill metadata, role TOML and local Markdown references offline."""
from pathlib import Path
import re
import sys
import tomllib


def validate(root):
    root = root.resolve()
    errors = []
    skills = list((root / '.agents/skills').glob('*/SKILL.md'))
    roles = list((root / '.codex/agents').glob('*.toml'))
    if not skills or not roles:
        errors.append('Project skills or roles are missing')
    names = set()
    for path in skills:
        text = path.read_text(encoding='utf-8')
        match = re.match(r'\A---\nname: ([a-z0-9-]{1,63})\ndescription: ([^\n]+)\n---\n', text)
        if not match or match[1] != path.parent.name or match[1] in names:
            errors.append(f'Invalid or duplicate skill metadata: {path.relative_to(root)}')
        elif match:
            names.add(match[1])
    role_names = set()
    for path in roles:
        try:
            data = tomllib.loads(path.read_text(encoding='utf-8'))
            if any(not isinstance(data.get(key), str) or not data[key].strip()
                   for key in ('name', 'description', 'developer_instructions')):
                raise ValueError('Missing role fields')
            if data['name'] in role_names:
                raise ValueError('Duplicate role name')
            role_names.add(data['name'])
        except (tomllib.TOMLDecodeError, ValueError):
            errors.append(f'Invalid role metadata: {path.relative_to(root)}')
    markdown = [root / n for n in ('AGENTS.md', 'CLAUDE.md', 'README.md', 'README.en.md', 'TESTING.md')]
    for directory in ('docs', 'tools', '.agents', '.github', 'deploy', 'hardware'):
        markdown.extend((root / directory).rglob('*.md'))
    for path in markdown:
        if not path.exists():
            errors.append(f'Missing document: {path.relative_to(root)}')
            continue
        text = path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)\s]+)\)', text):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            target = target.split('#', 1)[0]
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                errors.append(f'Broken/outside link in {path.relative_to(root)}: {target}')
    return errors


def main():
    errors = validate(Path(__file__).resolve().parents[1])
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print('Project skill metadata, role TOML and local Markdown links are valid.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
