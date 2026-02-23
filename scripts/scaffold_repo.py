from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tkinter as tk
from tkinter import filedialog

TREE_LINE_RE = re.compile(
    r"^(?P<prefix>(?:│\s{3}|\s{4})*)(?:[├└]──\s*)?(?P<node>.+?)\s*$"
)
TREE_INDENT_RE = re.compile(r"(?:│\s{3}|\s{4})")
ROOT_SENTINELS = {"project_root", "root", "."}


# ============================================================
# Helpers
# ============================================================

def touch_init(folder: Path):
    """Crea __init__.py para módulos Python."""
    (folder / "__init__.py").touch(exist_ok=True)


def select_destination_folder() -> Path:
    """Explorador para seleccionar carpeta destino."""
    root = tk.Tk()
    root.withdraw()

    print("\n📂 Selecciona la carpeta DESTINO donde se creará el proyecto...\n")

    selected = filedialog.askdirectory(
        title="Selecciona carpeta destino del proyecto"
    )

    if not selected:
        raise SystemExit("❌ No seleccionaste ninguna carpeta. Cancelado.")

    return Path(selected)


def load_template(templates_dir: Path, template_name: str) -> str:
    """Carga template desde un directorio definido por el usuario."""
    template_path = templates_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"❌ No existe el template: {template_path}")

    return template_path.read_text(encoding="utf-8")


def _extract_tree_lines(template_text: str) -> list[str]:
    """Extrae líneas candidatas del árbol, priorizando bloques ```."""
    lines = template_text.splitlines()
    tree_lines: list[str] = []
    in_code_block = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            tree_lines.append(raw_line)

    return tree_lines or lines


def _is_safe_relative_path(path_str: str) -> bool:
    """Valida que el path relativo no haga traversal ni sea absoluto."""
    if not path_str.strip():
        return False

    path = PurePosixPath(path_str)

    if path.is_absolute():
        return False

    if any(part in {"", ".", ".."} for part in path.parts):
        return False

    return True


def parse_tree_template(template_text: str) -> tuple[list[str], str]:
    """
    Parsea template de árbol y retorna:
    - carpetas relativas a crear (posix style)
    - texto limpio del treemap para docs/treemap.md
    """
    cleaned_treemap = template_text.rstrip() + "\n"
    lines = _extract_tree_lines(cleaned_treemap)

    folders: list[str] = []
    seen: set[str] = set()
    stack: list[str] = []

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        line = line.replace("\t", "    ")
        match = TREE_LINE_RE.match(line)
        if not match:
            continue

        prefix = match.group("prefix") or ""
        depth = len(TREE_INDENT_RE.findall(prefix))
        node = (match.group("node") or "").strip().strip("`")

        if not node:
            continue

        is_dir = node.endswith("/")
        name = node[:-1].strip() if is_dir else node

        if not name:
            continue

        if depth < len(stack):
            stack = stack[:depth]
        elif depth > len(stack):
            depth = len(stack)

        if is_dir and depth == 0 and name.lower() in ROOT_SENTINELS:
            stack = []
            continue

        if not is_dir:
            continue

        candidate_parts = [*stack, name]
        rel_path = PurePosixPath(*candidate_parts).as_posix()

        if not _is_safe_relative_path(rel_path):
            continue

        if rel_path not in seen:
            seen.add(rel_path)
            folders.append(rel_path)

        stack = candidate_parts

    return folders, cleaned_treemap


def copy_reusable_files(templates_dir: Path, project_root: Path):
    """
    Copia templates/reusable_files → scripts/reusable_files
    """
    source = templates_dir / "reusable_files"
    destination = project_root / "scripts/reusable_files"

    if not source.exists():
        print("⚠️ No existe templates/reusable_files. Saltando copia.")
        return

    shutil.copytree(source, destination, dirs_exist_ok=True)
    print("📦 Copied reusable_files into scripts/reusable_files")


def _create_folders_from_template(project_root: Path, folder_paths: list[str]):
    """Crea carpetas parseadas desde template con validación de seguridad."""
    project_root_resolved = project_root.resolve()

    for rel_posix_path in folder_paths:
        if not _is_safe_relative_path(rel_posix_path):
            continue

        rel_os_path = Path(*PurePosixPath(rel_posix_path).parts)
        target_path = project_root / rel_os_path

        try:
            target_path.resolve().relative_to(project_root_resolved)
        except ValueError:
            continue

        target_path.mkdir(parents=True, exist_ok=True)

        if rel_os_path.parts and rel_os_path.parts[0] == "src":
            touch_init(target_path)


def create_project(project_root: Path, templates_dir: Path, include_reusable: bool):
    """
    Genera carpetas + archivos base desde templates.
    Opcionalmente copia reusable_files.
    """
    print(f"\n📦 Creando skeleton en:\n   {project_root}\n")

    # --- Cargar y parsear estructura canónica del proyecto ---
    treemap_template_text = load_template(templates_dir, "etl_local.template")
    folder_paths, _ = parse_tree_template(treemap_template_text)

    if not folder_paths:
        raise ValueError(
            "❌ No se detectaron carpetas válidas en etl_local.template."
        )

    # --- Crear carpetas según template ---
    _create_folders_from_template(project_root, folder_paths)

    # --- Archivos desde templates ---
    template_map = {
        ".gitignore": "gitignore.template",
        "requirements.txt": "requirements.template",
    }

    for target, template_file in template_map.items():
        content = load_template(templates_dir, template_file)

        filepath = project_root / target
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        print(f"📄 Created: {target}")

    # --- Opción reusable_files ---
    if include_reusable:
        copy_reusable_files(templates_dir, project_root)

    print("\n🚀 Proyecto generado correctamente.\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("   ETL LOCAL PROJECT SCAFFOLD ")
    print("==============================\n")

    # Nombre del proyecto
    project_name = (
        sys.argv[1].strip()
        if len(sys.argv) > 1
        else input("📌 Nombre del proyecto: ").strip()
    )
    if not project_name:
        raise SystemExit("❌ Nombre inválido.")

    # Ruta de templates (siempre relativa al script)
    templates_dir = Path(__file__).resolve().parent / "templates"
    print(f"📁 Templates path: {templates_dir}")

    if not templates_dir.exists():
        raise SystemExit(f"❌ La ruta de templates no existe: {templates_dir}")

    # Opción reusable_files
    reusable_choice = input(
        "📌 ¿Copiar reusable_files starter kit? (y/n): "
    ).strip().lower()

    include_reusable = reusable_choice == "y"

    # Carpeta destino seleccionada por explorador
    destination = select_destination_folder()

    # Root del proyecto
    project_root = destination / project_name

    if project_root.exists():
        raise SystemExit("❌ Ya existe un proyecto con ese nombre.")

    project_root.mkdir()

    # Crear proyecto
    create_project(project_root, templates_dir, include_reusable)
