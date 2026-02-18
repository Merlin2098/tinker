from pathlib import Path
import tkinter as tk
from tkinter import filedialog


# ============================================================
# Folder Skeleton (ETL Local - Generic)
# ============================================================

FOLDERS = [

    # --- Config declarativa ---
    "src/config/json",
    "src/config/yaml",
    "src/config/sql",
    "src/config/ui/icon",
    "src/config/ui/themes",

    # --- Core ETL (vacío, depende del proyecto) ---
    "src/core",

    # --- UI Desktop ---
    "src/ui/widgets",
    "src/ui/workers",

    # --- Utils transversales ---
    "src/utils/core",
    "src/utils/etl/converters",
    "src/utils/etl/database",
    "src/utils/etl/validators",
    "src/utils/formatting",
    "src/utils/logs",
    "src/utils/ui",

    # --- Extra ---
    "tests",
    "scripts",
    "docs",
]


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


def create_project(project_root: Path, templates_dir: Path):
    """Genera carpetas + archivos base desde templates."""
    print(f"\n📦 Creando skeleton en:\n   {project_root}\n")

    # --- Crear carpetas ---
    for folder in FOLDERS:
        path = project_root / folder
        path.mkdir(parents=True, exist_ok=True)

        if folder.startswith("src/"):
            touch_init(path)

    # --- Archivos desde templates ---
    template_map = {
        ".gitignore": "gitignore.template",
        "requirements.txt": "requirements.template",
        "docs/treemap.md": "etl_local.template",
    }

    for target, template_file in template_map.items():
        content = load_template(templates_dir, template_file)

        filepath = project_root / target
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

        print(f"📄 Created: {target}")

    print("\n🚀 Proyecto generado correctamente.\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("   ETL LOCAL PROJECT SCAFFOLD ")
    print("==============================\n")

    # Nombre del proyecto
    project_name = input("📌 Nombre del proyecto: ").strip()
    if not project_name:
        raise SystemExit("❌ Nombre inválido.")

    # Ruta de templates
    templates_path_str = input(
        "📌 Ruta de templates (ej: C:/Dev/templates): "
    ).strip()

    templates_dir = Path(templates_path_str)

    if not templates_dir.exists():
        raise SystemExit("❌ La ruta de templates no existe.")

    # Carpeta destino seleccionada por explorador
    destination = select_destination_folder()

    # Root del proyecto
    project_root = destination / project_name

    if project_root.exists():
        raise SystemExit("❌ Ya existe un proyecto con ese nombre.")

    project_root.mkdir()

    # Crear proyecto
    create_project(project_root, templates_dir)