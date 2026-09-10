"""Build and exercise an isolated wheel using checks from its source archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.request
import zipfile

from check_distribution import candidate_files, check_file, require, sha

CFF_SCHEMA_URL = 'https://raw.githubusercontent.com/citation-file-format/citation-file-format/1.2.0/schema.json'
CFF_SCHEMA_SHA256 = '0b8d22140da702d766df318dcff3a91af2f39521298dcf36d76315fd99cc169b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cff-schema', type=Path, help='Optional local copy of the checksum-pinned official schema')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    logs = output / 'logs'
    logs.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in {'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'UV_PROJECT_ENVIRONMENT'}}
    env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', UV_LINK_MODE='copy')
    commands = []

    def run(label, arguments, cwd):
        result = subprocess.run([str(x) for x in arguments], cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8')
        (logs / f'{label}.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        commands.append({'check': label, 'exit_code': result.returncode})
        require(result.returncode == 0, f'{label} failed: {result.stderr[-3500:]}')
        return result

    import yaml
    import jsonschema
    raw_schema = args.cff_schema.read_bytes() if args.cff_schema else urllib.request.urlopen(CFF_SCHEMA_URL, timeout=30).read()
    require(sha(raw_schema) == CFF_SCHEMA_SHA256, 'Citation schema checksum changed')
    citation = yaml.safe_load((root / 'CITATION.cff').read_text(encoding='utf-8'))
    jsonschema.validate(citation, json.loads(raw_schema))
    project = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))['project']
    require(citation['version'] == project['version'] and citation['license'] == project['license'], 'Citation metadata mismatch')
    inventory = candidate_files(root)
    dist = output / 'dist'
    dist.mkdir(exist_ok=True)
    require(not any(dist.iterdir()), 'Use a fresh output directory for release verification')
    run('build', ['uv', 'build', '--out-dir', dist], root)
    wheels, sdists = list(dist.glob('*.whl')), list(dist.glob('*.tar.gz'))
    require(len(wheels) == len(sdists) == 1, 'Expected one wheel and one source archive')
    wheel, sdist = wheels[0], sdists[0]
    with zipfile.ZipFile(wheel) as archive:
        package = {x['path'].removeprefix('src/') for x in inventory if x['path'].startswith('src/')}
        require({n for n in archive.namelist() if '.dist-info/' not in n} == package, 'Wheel file inventory mismatch')
        for name in package:
            require(archive.read(name) == (root / 'src' / name).read_bytes(), f'Wheel/source mismatch: {name}')
        for name in archive.namelist():
            if '.dist-info/' not in name:
                continue
            leaf = name.split('.dist-info/', 1)[1]
            require(leaf in {'METADATA', 'WHEEL', 'RECORD', 'entry_points.txt', 'licenses/LICENSE', 'licenses/LICENSE_SCOPE.md', 'licenses/THIRD_PARTY_NOTICES.md'}, 'Unexpected wheel metadata')
            if leaf.startswith('licenses/'):
                require(archive.read(name) == (root / leaf.removeprefix('licenses/')).read_bytes(), 'Wheel license mismatch')
        metadata = archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))).decode()
        requirements = re.findall(r'^Requires-Dist: (.+)$', metadata, re.M)
        require(set(requirements) == {"matplotlib==3.10.7; extra == 'figures'", "numpy==2.4.6; extra == 'figures'"}, 'Unexpected wheel runtime dependencies')

    with tempfile.TemporaryDirectory(prefix='rcms-release-') as temporary:
        scratch = Path(temporary).resolve()
        with tarfile.open(sdist) as archive:
            for member in archive.getmembers():
                require(member.isfile() and not member.issym() and not member.islnk() and not member.name.startswith('/') and '..' not in Path(member.name).parts, 'Unsafe source archive member')
            archive.extractall(scratch / 'source', filter='data')
        source = next((scratch / 'source').iterdir())
        names = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
        require(names == {x['path'] for x in inventory} | {'PKG-INFO'}, 'Source archive inventory mismatch')
        for item in inventory:
            require((source / item['path']).read_bytes() == (root / item['path']).read_bytes(), f'Source archive bytes differ: {item["path"]}')
        venv = scratch / 'venv'
        python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        run('create-environment', ['uv', 'venv', '--python', sys.executable, venv], scratch)
        run('install-wheel', ['uv', 'pip', 'install', '--python', python, '--no-index', '--no-deps', wheel], scratch)
        base = run('base-without-plotting', [python, '-I', '-c', 'import importlib.util; import risk_controlled_segmentation as p; assert importlib.util.find_spec("matplotlib") is None; print(p.__file__); print(p.__version__)'], scratch)
        origin, version = base.stdout.strip().splitlines()
        require(Path(origin).resolve().is_relative_to(venv) and version == project['version'], 'Wheel import/version mismatch')
        # Installed code may not read either the candidate or extracted source.
        guard = '''import os, runpy, sys
from pathlib import Path
blocked = [Path(x).resolve() for x in os.environ['RCMS_BLOCKED_ROOTS'].split(os.pathsep)]
def audit(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('Runtime network access is forbidden')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        if any(path.is_relative_to(root) for root in blocked):
            raise RuntimeError('Source checkout access is forbidden')
sys.addaudithook(audit)
sys.argv = ['rcms'] + sys.argv[1:]
runpy.run_module('risk_controlled_segmentation', run_name='__main__')
'''
        env['RCMS_BLOCKED_ROOTS'] = os.pathsep.join([str(root), str(source)])
        env['MPLCONFIGDIR'] = str(scratch / 'mpl-cache')

        def cli(label, *arguments):
            return run(label, [python, '-I', '-c', guard, *arguments], scratch)

        cli('demo', 'demo')
        verification = json.loads(cli('verify', 'verify').stdout)
        require(verification['final_calibrations_replayed'] == 8 and verification['warmup_aggregate_runs'] == 902, 'Study inventory mismatch')
        for study in ('chaksu', 'riga'):
            cli(study, study, '--output', scratch / study)
            require((scratch / study / 'report.md').read_text(encoding='utf-8') == (source / 'experiments' / study / 'report.md').read_text(encoding='utf-8'), f'{study} report text changed')
            for path in (scratch / study).iterdir():
                target = output / study / path.name
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(path.read_bytes())
        tests = run('tests-from-sdist', [python, '-I', '-m', 'unittest', 'discover', '-s', source / 'tests', '-v'], scratch)
        match = re.search(r'Ran (\d+) tests', tests.stderr)
        require(match is not None and int(match.group(1)) == 34, 'Test suite inventory changed')
        reference = json.loads(run('reference-from-sdist', [python, '-I', source / 'scripts/verify_reference.py'], scratch).stdout)
        require(reference['synthetic_cases'] == 2000, 'Reference scope changed')
        requirements_path = scratch / 'figures-requirements.txt'
        run('export-figure-lock', ['uv', 'export', '--locked', '--extra', 'figures', '--no-emit-project', '--output-file', requirements_path], source)
        run('install-figure-lock', ['uv', 'pip', 'install', '--python', python, '--require-hashes', '-r', requirements_path], scratch)
        # Data comparison in the parent process: the CLI never needs checkout access.
        from risk_controlled_segmentation.study import compare
        first, second = scratch / 'figures-first', scratch / 'figures-second'
        cli('figures-first', 'figures', '--output', first)
        cli('figures-second', 'figures', '--output', second)
        expected = json.loads((source / 'docs/figures/plot_data.json').read_text(encoding='utf-8'))
        actual = json.loads((first / 'plot_data.json').read_text(encoding='utf-8'))
        compare(actual, expected)
        from risk_controlled_segmentation.figures import STEMS
        figure_names = {stem + suffix for stem in STEMS for suffix in ('.svg', '.png')} | {'plot_data.json'}
        require({p.name for p in first.iterdir()} == figure_names, 'Figure inventory changed')
        for name in sorted(figure_names):
            require((first / name).read_bytes() == (second / name).read_bytes(), f'Non-deterministic local figure: {name}')
            check_file('docs/figures/' + name, (first / name).read_bytes())
            target = output / 'figures' / name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes((first / name).read_bytes())
        # The validation CLI checks a scratch copy, still with checkout/network blocked.
        cli('verify-figures', 'verify-figures', first / 'plot_data.json')

    receipt = {'status': 'PASS', 'python': platform.python_version(), 'system': platform.system(),
               'candidate_files': len(inventory), 'wheel_package_files': len(package), 'unit_tests': 34,
               'reference_synthetic_cases': 2000, 'final_calibrations': 8, 'warmup_aggregate_runs': 902,
               'citation_schema_sha256': CFF_SCHEMA_SHA256,
               'base_without_plotting_dependencies': True, 'report_text_matches': True,
               'figure_data_absolute_tolerance': 1e-12, 'figure_pairs': len(STEMS),
               'same_environment_figure_bytes_deterministic': True,
               'runtime_network_and_both_source_checkouts_blocked': True,
               'wheel': {'filename': wheel.name, 'sha256': sha(wheel.read_bytes())},
               'sdist': {'filename': sdist.name, 'sha256': sha(sdist.read_bytes())}, 'commands': commands}
    (output / 'checks.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({key: receipt[key] for key in ('status', 'unit_tests', 'reference_synthetic_cases', 'figure_pairs')}))


if __name__ == '__main__':
    main()
