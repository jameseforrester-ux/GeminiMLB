"""Run this script on the server to rewrite all core bot files cleanly."""
import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))

def write(rel, content):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {rel}")

# Touch __init__ files
for pkg in ["app", "app/bot", "app/services", "app/models", "app/utils", "app/data"]:
    p = os.path.join(ROOT, pkg, "__init__.py")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "a").close()

print("All __init__.py files created")

# Verify main.py is importable
try:
    import ast
    for rel in ["app/main.py", "app/bot/application.py", "app/bot/handlers.py",
                "app/utils/formatting.py", "app/services/betting_service.py",
                "app/services/odds_provider.py", "app/services/projection_engine.py"]:
        path = os.path.join(ROOT, rel)
        if os.path.exists(path):
            with open(path) as f:
                ast.parse(f.read())
            print(f"  OK syntax: {rel}")
        else:
            print(f"  MISSING: {rel}")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)

print("All checks passed!")
