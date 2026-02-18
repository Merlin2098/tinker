from pathlib import Path
import tkinter as tk
from tkinter import filedialog


# ============================================================
# Skeleton oficial del proyecto (basado en tu arquitectura real)
# ============================================================

FOLDERS = [

    # --- SRC base ---
    "src/config/json",
    "src/config/yaml",
    "src/config/sql",
    "src/config/ui/icon",
    "src/config/ui/themes",

    "src/core/people_point",
    "src/core/bd_yoly",
    "src/core/contrast",

    "src/ui/widgets",
    "src/ui/workers",

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

FILES = {
    "main.py": """\
if __name__ == "__main__":
    print("Booting ETL Desktop App...")
""",
    "docs/architecture.md": "# Arquitectura del Proyecto\n\n(Generado automáticamente)\n",
    "instructions_dev.md": "# Developer Notes\n\nPendiente.\n",
}


# ============================================================
# Helpers
# ============================================================

def touch_init(folder: Path):
    """Crea __init__.py para módulos Python."""
    init_file = folder / "__init__.py"
    init_file.touch(exist_ok=True)


def select_destination_folder() -> Path:
    """
    Abre explorador para que el usuario seleccione
    la carpeta donde se creará el proyecto.
    """
    root = tk.Tk()
    root.withdraw()

    print("\n📂 Selecciona la carpeta DESTINO donde se creará el proyecto...\n")

    selected = filedialog.askdirectory(
        title="Selecciona carpeta destino del proyecto"
    )

    if not selected:
        raise SystemExit("❌ No seleccionaste ninguna carpeta. Cancelado.")

    return Path(selected)


def create_project(project_root: Path):
    """
    Crea toda la estructura dentro de project_root.
    """
    print(f"\n📦 Creando skeleton en:\n   {project_root}\n")

    # Crear carpetas
    for folder in FOLDERS:
        path = project_root / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Folder: {folder}")

        if folder.startswith("src/"):
            touch_init(path)

    # Crear archivos base
    for file, content in FILES.items():
        filepath = project_root / file

        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
            print(f"📄 File created: {file}")
        else:
            print(f"⚠️ Already exists: {file}")

    print("\n🚀 Proyecto generado correctamente.\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("   PROJECT SCAFFOLD GENERATOR ")
    print("==============================\n")

    # 1. Nombre del proyecto
    project_name = input("📌 Ingresa el nombre del proyecto: ").strip()

    if not project_name:
        raise SystemExit("❌ Nombre inválido. Cancelado.")

    # 2. Seleccionar carpeta destino (padre)
    destination_folder = select_destination_folder()

    # 3. Crear carpeta del proyecto dentro del destino
    project_root = destination_folder / project_name

    if project_root.exists():
        raise SystemExit(
            f"❌ Ya existe una carpeta llamada '{project_name}' en:\n   {destination_folder}"
        )

    project_root.mkdir()

    # 4. Generar estructura
    create_project(project_root)
