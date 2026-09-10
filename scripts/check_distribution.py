"""Review the candidate and reachable Git history against the public file boundary."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT_FILES = {'.gitattributes', '.gitignore', 'README.md', 'LICENSE', 'LICENSE_SCOPE.md',
              'THIRD_PARTY_NOTICES.md', 'CITATION.cff', 'pyproject.toml', 'uv.lock'}
FIGURES = {'transfer_tradeoff', 'risk_area_budgets', 'calibration_size',
           'disagreement_and_sources', 'synthetic_omission'}
EVIDENCE = {'calibration_curve', 'context', 'development', 'final',
            'warmup_runs', 'warmup_expected', 'manifest'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_file(name, data):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name, 'Unsafe path')
    require(len(data) <= 5_000_000, f'Unexpected file size: {name}')
    allowed = name in ROOT_FILES
    allowed |= path.parent.as_posix() in {'scripts', 'tests', 'src/risk_controlled_segmentation'} and path.suffix == '.py'
    allowed |= path.parent.as_posix() == 'reference' and path.suffix in {'.md', '.ts', '.mts'}
    allowed |= path.parts[0] in {'docs', 'experiments'} and path.suffix == '.md'
    allowed |= name == '.github/workflows/research.yml'
    allowed |= name == 'docs/figures/plot_data.json'
    allowed |= path.parent.as_posix() == 'docs/figures' and path.stem in FIGURES and path.suffix in {'.svg', '.png'}
    allowed |= path.parent.as_posix() in {'src/risk_controlled_segmentation/evidence/chaksu', 'src/risk_controlled_segmentation/evidence/riga'} and path.stem in EVIDENCE and path.suffix == '.json'
    require(allowed, f'File outside reviewed scope: {name}')
    if path.suffix == '.png':
        require(data.startswith(b'\x89PNG\r\n\x1a\n'), f'Invalid figure PNG: {name}')
        return
    text = data.decode('utf-8')
    private_prefixes = ['/' + part + '/' for part in ('Users', 'Volumes')]
    private_prefixes += ['PRODUCT' + '/', 'file' + '://']
    require(not any(x in text for x in private_prefixes), f'Private path in {name}')
    if path.suffix == '.svg':
        require('<svg' in text and '<image' not in text and '<script' not in text and 'data:image' not in text,
                f'Unexpected embedded content in figure: {name}')
    if path.suffix == '.json':
        def visit(value):
            if isinstance(value, dict):
                forbidden = {'image_id', 'patient_id', 'opaque_identity', 'unit_id', 'score_path',
                             'mask_path', 'expert_mask_areas', 'q_numerators'}
                require(not forbidden.intersection(value), f'Row-level field in {name}')
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(json.loads(text))


def candidate_files(root):
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root).decode().split('\0')
    result = []
    for name in sorted(set(names) - {''}):
        path = root / name
        require(path.is_file() and not path.is_symlink(), f'Ordinary file required: {name}')
        data = path.read_bytes()
        check_file(name, data)
        result.append({'path': name, 'sha256': sha(data), 'bytes': len(data)})
    return result


def check_links(root, items):
    count = 0
    for item in items:
        if not item['path'].endswith('.md'):
            continue
        path = root / item['path']
        for target in re.findall(r'\]\(([^\s)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#', 1)[0]
            resolved = (path.parent / target).resolve()
            require(resolved.is_relative_to(root) and resolved.exists(), f'Broken local link in {item["path"]}: {target}')
            count += 1
    return count


def check_history(root):
    require(subprocess.check_output(['git', 'rev-parse', '--is-shallow-repository'], cwd=root, text=True).strip() == 'false',
            'Complete history is required')
    commits = subprocess.check_output(['git', 'rev-list', '--all'], cwd=root, text=True).splitlines()
    seen = set()
    for commit in commits:
        tree = subprocess.check_output(['git', 'ls-tree', '-rz', commit], cwd=root).decode().split('\0')
        for entry in filter(None, tree):
            header, name = entry.split('\t', 1)
            mode, kind, oid = header.split()
            require(kind == 'blob' and mode in {'100644', '100755'}, 'Unexpected tree entry')
            if (name, oid) not in seen:
                check_file(name, subprocess.check_output(['git', 'cat-file', 'blob', oid], cwd=root))
                seen.add((name, oid))
    return {'commits': len(commits), 'unique_path_blob_pairs': len(seen)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    items = candidate_files(root)
    result = {'status': 'PASS', 'files': items, 'local_links_checked': check_links(root, items),
              'history': check_history(root) if args.history else None,
              'scope': 'Specified file/content boundary; separate secret scan and scientific review required.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'candidate_files': len(items), 'history': result['history']}))


if __name__ == '__main__':
    main()
