"""Inspect documentation and Python syntax without executing project code."""
import ast
import os
import re
from pathlib import Path
from .phrases import SCREENRECORDING, NOSCREENRECORDING, GENERIC_NAMES


def normalize(text):
    return ' '.join(text.lower().replace('’', "'").replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


def paragraphs(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            lines.append('')
        elif mark:
            fence = mark.group(1)
            lines.append('')
        else:
            lines.append(line)
    return [normalize(p) for p in re.split(r'\n\s*\n', '\n'.join(lines)) if p.strip()]


def evidence(source):
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except (SyntaxError, ValueError):
        return False
    imports, shadows, definitions = {}, set(), set()
    def names(target):
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return set().union(*(names(x) for x in target.elts))
        if isinstance(target, ast.Starred):
            return names(target.value)
        return set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for a in node.names:
                imports[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            for a in node.names:
                imports[a.asname or a.name] = (node.module or '') + '.' + a.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
            shadows.add(node.name)
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [x.optional_vars for x in node.items if x.optional_vars]
        for target in targets:
            shadows.update(names(target))
    flags = set()
    has_mss = any(v == 'mss' or v.startswith('mss.') for v in imports.values())
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        resolved = ''
        if isinstance(func, ast.Name):
            if func.id not in shadows:
                resolved = imports.get(func.id, '')
            name = resolved.rsplit('.', 1)[-1]
        elif isinstance(func, ast.Attribute):
            name = func.attr
            base = func.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                if base.id in imports and base.id in shadows:
                    continue
                resolved = imports.get(base.id, '')
        else:
            continue
        if name in definitions:
            continue
        if name in GENERIC_NAMES and (isinstance(func, ast.Attribute) or resolved):
            return True
        def route(targets, roots, attr):
            return (isinstance(func, ast.Name) and resolved in targets) or (isinstance(func, ast.Attribute) and name == attr and resolved in roots)
        if route({'ffmpeg.input'}, {'ffmpeg'}, 'input') and any(k.arg in {'f', 'format'} and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str) and k.value.value.lower() in {'x11grab', 'gdigrab', 'avfoundation', 'dshow', 'decklink', 'kmsgrab'} for k in node.keywords):
            flags.add('input')
        if route({'ffmpeg.output', 'ffmpeg.run'}, {'ffmpeg'}, 'output') or route({'ffmpeg.run'}, {'ffmpeg'}, 'run') or (isinstance(func, ast.Attribute) and name == 'run'):
            flags.add('output')
        if route({'cv2.VideoWriter'}, {'cv2'}, 'VideoWriter'):
            flags.add('writer')
        if route({'pyautogui.screenshot'}, {'pyautogui'}, 'screenshot') or route({'PIL.ImageGrab.grab'}, {'PIL.ImageGrab'}, 'grab') or (isinstance(func, ast.Attribute) and name in {'shot', 'grab'} and has_mss):
            flags.add('frame')
        if route({'pyscreenrec.ScreenRecorder'}, {'pyscreenrec'}, 'ScreenRecorder'):
            flags.add('recorder')
        if route({'vidgear.ScreenGear', 'vidgear.gears.ScreenGear'}, {'vidgear', 'vidgear.gears'}, 'ScreenGear'):
            flags.add('gear')
        if route({'obsws_python.ReqClient'}, {'obsws_python'}, 'ReqClient'):
            flags.add('client')
        if isinstance(func, ast.Attribute) and name in {'start_recording', 'start', 'start_record'}:
            flags.add(name)
    return any(set(pair) <= flags for pair in (('input', 'output'), ('writer', 'frame'), ('recorder', 'start_recording'), ('gear', 'start'), ('client', 'start_record')))



def audit(root, ignore=(), fail_on='high'):
    root = Path(root)
    if not root.is_dir() or not os.access(str(root), os.R_OK | os.X_OK):
        raise OSError('Not a readable directory: {}'.format(root))
    claims = denials = production = tests = False
    yes_re, no_re = pattern(SCREENRECORDING), pattern(NOSCREENRECORDING)
    for directory, dirs, files in os.walk(str(root), followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        parent = Path(directory)
        def ignored(path):
            rel = path.relative_to(root).as_posix()
            return any(rel == p.rstrip('/') or rel.startswith(p.rstrip('/') + '/') for p in ignore)
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink() and not ignored(parent / d))
        for filename in sorted(files):
            path = parent / filename
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            if (rel.as_posix() == 'README.md' or ('docs' in rel.parts and path.suffix == '.md')):
                for para in paragraphs(path.read_text(encoding='utf-8')):
                    denials |= bool(no_re.search(para))
                    claims |= bool(yes_re.search(no_re.sub(' ', para)))
            if path.suffix == '.py' and not any(x in rel.parts for x in ('fixtures', 'docs', 'examples')):
                is_test = 'tests' in rel.parts or filename.startswith('test_') or filename.endswith('_test.py')
                if evidence(path.read_text(encoding='utf-8')):
                    if is_test:
                        tests = True
                    else:
                        production = True
    findings = []
    if claims and not production:
        severity = 'MEDIUM' if tests else 'HIGH'
        findings.append({'rule': 'documented-screen-recording-claim-false', 'severity': severity, 'message': 'Documented claim has ' + ('test-only evidence.' if tests else 'no production evidence.')})
    if denials and production:
        findings.append({'rule': 'documented-no-screen-recording-claim-false', 'severity': 'HIGH', 'message': 'Documented denial conflicts with production evidence.'})
    fail = any(f['severity'] == 'HIGH' or fail_on.lower() == 'medium' for f in findings)
    return {'verdict': 'FAIL' if fail else 'PASS', 'findings': findings}
