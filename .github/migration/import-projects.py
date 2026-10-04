import argparse
import ast
import gzip
import json
import os
import subprocess
from pathlib import Path


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def entries(ref):
    raw = subprocess.check_output(['git', 'ls-tree', '-r', '-z', ref])
    return {line.split(b'\t', 1)[1].decode(): line.split(b'\t', 1)[0]
            for line in raw.split(b'\0') if line}


parser = argparse.ArgumentParser()
parser.add_argument('--local-sources', type=Path)
args = parser.parse_args()
root = Path.cwd()
manifest = json.loads(Path('.github/migration/manifest.json').read_text())
overlays = json.loads(gzip.decompress(Path('.github/migration/overlays.json.gz').read_bytes()))
base = git('rev-parse', 'HEAD')
assert not git('status', '--porcelain'), 'Worktree must be clean'

for item in manifest:
    repo, prefix, source = item['repository'], item['prefix'], item['sha']
    assert not (root / prefix).exists(), f'{prefix} already exists'
    remote = str(args.local_sources / repo) if args.local_sources else f'https://github.com/Show-o4210/{repo}.git'
    git('fetch', '--no-tags', remote, source)
    assert int(git('rev-list', '--count', source)) == item['count']
    git('read-tree', '--prefix=' + prefix + '/', '-u', source)
    tree = git('write-tree')
    imported = git('commit-tree', tree, '-p', git('rev-parse', 'HEAD'), '-p', source,
                   '-m', f'Import {repo} into {prefix} with original history')
    git('reset', '--hard', imported)
    assert git('rev-parse', 'HEAD:' + prefix) == git('rev-parse', source + '^{tree}')
    print(f'Imported {repo}: exact tree and {item["count"]} original commits', flush=True)

for relative, text in overlays.items():
    path = root / relative
    assert path.resolve().is_relative_to(root) and '.git' not in path.parts
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

# Remove the one-time importer and workflow from the finished repository.
git('rm', '-r', '.github/migration', '.github/workflows/import-projects-once.yml')
git('add', '-A')
git('commit', '-m', 'Document monorepo entry points, migration provenance and license boundaries')

for item in manifest:
    git('merge-base', '--is-ancestor', item['sha'], 'HEAD')
    source_entries = entries(item['sha'])
    target_entries = entries('HEAD:' + item['prefix'])
    assert source_entries.keys() == target_entries.keys(), f'Missing or extra paths in {item["prefix"]}'
    for path, original in source_entries.items():
        if path != 'README.md':
            assert target_entries[path] == original, f'Changed source: {item["prefix"]}/{path}'
    for path in (root / item['prefix']).rglob('*.py'):
        ast.parse(path.read_bytes(), filename=str(path))
    print(f'Validated {item["prefix"]}: history, paths, modes, blobs and Python syntax', flush=True)

git('merge-base', '--is-ancestor', base, 'HEAD')
assert not git('status', '--porcelain'), 'Unexpected uncommitted files'
# Source blobs are preserved exactly, including existing Markdown hard breaks.
git('diff', '--exit-code', 'HEAD', '--')
print('Finished migration:', git('rev-parse', 'HEAD'), flush=True)
