"""Check local Markdown/image targets and chapter README files without network access."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote

def check(root):
    docs = sorted(p for p in root.rglob('*.md') if '.git' not in p.parts)
    broken, checked, external = [], 0, 0
    for path in docs:
        source = re.sub(r'```[\s\S]*?```', '', path.read_text(encoding='utf-8-sig'))
        targets = re.findall(r'!?\[[^\]\n]*\]\((<[^>]+>|[^)]+)\)', source)
        targets += re.findall(r'<(?:img|a)\b[^>]*?(?:src|href)=["\']([^"\']+)', source)
        for target in targets:
            target = target.strip().strip('<>')
            if re.match(r'^(?:https?://|mailto:|app:|codex:|data:)', target):
                external += 1
                continue
            if target.startswith('#'):
                continue
            target = unquote(target.split('#', 1)[0].split('?', 1)[0])
            if not target:
                continue
            checked += 1
            if not (path.parent/target).exists():
                broken.append({'file': path.relative_to(root).as_posix(), 'target': target})
    chapters = sorted(p for p in root.iterdir() if p.is_dir() and re.match(r'^\d{2}\.', p.name))
    missing = [p.name for p in chapters if not (p/'README.md').exists()]
    return {'markdown_files': len(docs), 'chapters': len(chapters),
            'missing_chapter_readmes': missing, 'local_links_checked': checked,
            'external_links_not_verified': external, 'broken_local_links': broken,
            'result': 'PASS' if not broken and not missing else 'FAIL'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = check(args.repo.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['result'] == 'PASS' else 1)

if __name__ == '__main__':
    main()
