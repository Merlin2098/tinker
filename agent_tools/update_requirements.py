import subprocess
import sys
import os
import io
import json
import re
from typing import Iterable

# Forzamos que la salida estándar use UTF-8 para evitar errores de codificación con emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ALWAYS_KEEP = {"pip", "setuptools", "wheel"}


def normalize_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)")


def extract_req_name(line: str) -> str | None:
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    # Ignore include/constraints/find-links and other pip options
    if raw.startswith(("-r", "--", "-c", "-f")):
        return None
    if raw.startswith("-e"):
        egg = re.search(r"#egg=([A-Za-z0-9_.-]+)", raw)
        return normalize_name(egg.group(1)) if egg else None
    # Direct reference: name @ url
    if " @ " in raw:
        left = raw.split(" @ ", 1)[0].strip()
        return normalize_name(left) if left else None
    egg = re.search(r"#egg=([A-Za-z0-9_.-]+)", raw)
    if egg:
        return normalize_name(egg.group(1))
    # Strip environment markers
    if ";" in raw:
        raw = raw.split(";", 1)[0].strip()
    m = _REQ_NAME_RE.match(raw)
    return normalize_name(m.group(1)) if m else None


def parse_requirements(path: str) -> set[str]:
    names: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = extract_req_name(line)
            if name:
                names.add(name)
    return names


def run_pip(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pip", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def list_installed() -> dict[str, str]:
    result = run_pip(["list", "--format=json"], check=True)
    data = json.loads(result.stdout or "[]")
    installed: dict[str, str] = {}
    for item in data:
        name = item.get("name")
        if not isinstance(name, str):
            continue
        installed[normalize_name(name)] = name
    return installed


def get_requires(name: str) -> set[str]:
    result = run_pip(["show", name], check=False)
    if result.returncode != 0:
        return set()
    requires: set[str] = set()
    for line in (result.stdout or "").splitlines():
        if line.startswith("Requires:"):
            raw = line.split(":", 1)[1].strip()
            if not raw:
                return set()
            for dep in raw.split(","):
                dep = dep.strip()
                if dep:
                    requires.add(normalize_name(dep))
            return requires
    return requires


def resolve_dependency_closure(roots: Iterable[str], installed: set[str]) -> set[str]:
    keep = set(roots)
    queue = list(roots)
    while queue:
        current = queue.pop()
        if current not in installed:
            continue
        for dep in get_requires(current):
            if dep not in keep:
                keep.add(dep)
                queue.append(dep)
    return keep


def run_update():
    # Usamos sys.executable para asegurar que usamos el Python del venv
    pip_command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

    print("--- Actualizando dependencias desde requirements.txt ---")

    try:
        # Ejecutamos pip install
        # check=True lanzará una excepción si el comando falla
        subprocess.run(pip_command, capture_output=True, text=True, check=True)
        print("[OK] Entorno virtual actualizado correctamente.")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudieron instalar las dependencias:")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ocurrio un error inesperado: {e}")
        sys.exit(1)

    # Sincronizar desinstalaciones con requirements.txt
    required = parse_requirements("requirements.txt")
    if not required:
        print("[INFO] No se encontraron dependencias explícitas. Saltando desinstalaciones.")
        return

    installed = list_installed()
    installed_names = set(installed.keys())
    keep = resolve_dependency_closure(required | ALWAYS_KEEP, installed_names)
    extras = sorted(installed_names - keep)

    if not extras:
        print("[OK] No hay dependencias extra para desinstalar.")
        return

    print(f"[INFO] Desinstalando {len(extras)} dependencias que no están en requirements.txt...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", *[installed[n] for n in extras]],
            capture_output=True,
            text=True,
            check=True,
        )
        print("[OK] Dependencias extra desinstaladas.")
    except subprocess.CalledProcessError as e:
        print("[ERROR] No se pudieron desinstalar las dependencias extra:")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ocurrio un error inesperado al desinstalar: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificamos si existe el archivo en la raíz (donde se ejecuta el git commit)
    if os.path.exists("requirements.txt"):
        run_update()
    else:
        print("[INFO] No se encontro requirements.txt. Saltando actualizacion.")
