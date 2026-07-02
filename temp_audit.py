"""Health audit script."""
import os

BASE = r"C:\Users\kbrat\PycharmProjects\GroundedAI"

terms = ['TODO', 'FIXME', 'placeholder', 'coming soon', 'implement later', 'dummy', 'stub', 'NotImplementedError']

print("=== FLAGGED TERMS ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    ll = line.lower()
                    for t in terms:
                        tl = t.lower()
                        if tl in ll:
                            print(f"  TERM:{t} | {rel}:{i}: {line.rstrip()[:130]}")
                            break

print("\n=== BARE `pass` STATEMENTS ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if line.strip() == 'pass':
                        print(f"  {rel}:{i}")

print("\n=== EMPTY / TINY FILES ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            size = os.path.getsize(fp)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
            if size < 20 or not content:
                print(f"  EMPTY | {rel} ({size} bytes)")
            elif len(content) < 80 and content.count('\n') == 0:
                print(f"  SINGLE_LINE | {rel}: {content[:80]}")

print("\n=== MISSING __init__.py ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        has_py = any(fn.endswith('.py') and fn != '__init__.py' for fn in filenames)
        if has_py and '__init__.py' not in filenames:
            rel = os.path.relpath(dirpath, BASE)
            print(f"  MISSING_INIT | {rel}/")

print("\n=== OLD-STYLE TYPING IMPORTS ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    s = line.strip()
                    if 'from typing import' in s and any(x in s for x in ['List', 'Optional', 'Dict', 'Tuple']):
                        print(f"  {rel}:{i}: {s[:120]}")

print("\n=== DUPLICATE MODULE-LEVEL ASSIGNMENTS ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            assigns = {}
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith('_') and not s.startswith('__') and '=' in s and not s.startswith('#'):
                    name = s.split('=')[0].strip()
                    if name and name.isidentifier():
                        if name in assigns:
                            print(f"  DUPLICATE | {rel}: {name} defined at lines {assigns[name]} and {i}")
                        else:
                            assigns[name] = i
                    assigns.setdefault(name, i)

print("\n=== __pycache__ DIRECTORIES (should be gitignored) ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '__pycache__' in dirpath:
            rel = os.path.relpath(dirpath, BASE)
            print(f"  PYCACHE | {rel}/")
        if '__pycache__' in dirnames:
            dirnames.remove('__pycache__')

print("\n=== NON-DETERMINISTIC `random` USAGE ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'random' in line.lower() and 'import' in line.lower():
                        print(f"  {rel}:{i}: {line.rstrip()[:130]}")
                    elif 'random.' in line.lower():
                        print(f"  {rel}:{i}: {line.rstrip()[:130]}")

print("\n=== DEPRECATED PYDANTIC Config CLASS ===")
for root in ['truthguard-ai', 'truthbench']:
    for dirpath, dirnames, filenames in os.walk(os.path.join(BASE, root)):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            dirnames.clear()
            continue
        for fn in filenames:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, BASE)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'class Config' in line and 'pydantic' in ''.join(f.readlines()[max(0,i-5):i]).lower():
                        print(f"  {rel}:{i}: {line.rstrip()[:130]}")
                    # Reset file position
                    f.seek(0)

print("\n=== ROOT main.py CHECK ===")
root_main = os.path.join(BASE, 'main.py')
if os.path.exists(root_main):
    with open(root_main, 'r') as f:
        c = f.read()
    if 'print_hi' in c or 'PyCharm' in c:
        print(f"  STUB_FILE | main.py: Default PyCharm template")

print("\n=== DONE ===")
