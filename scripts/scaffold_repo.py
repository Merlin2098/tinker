from pathlib import Path
import tkinter as tk
from tkinter import filedialog


# ============================================================
# Skeleton oficial del proyecto (basado en tu repo real)
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

    # Root entrypoint
    "main.py": """\
if __name__ == "__main__":
    print("Booting ETL Desktop App...")
""",

    # Docs
    "docs/architecture.md": "# Arquitectura del Proyecto\n\n(Generado automáticamente)\n",

    # Placeholder dev notes
    "instructions_dev.md": "# Developer Notes\n\nPendiente.\n",
}


# ============================================================
# Helpers
# ============================================================

def touch_init(folder: Path):
    """Crea __init__.py si es un módulo Python."""
    init_file = folder / "__init__.py"
    init_file.touch(exist_ok=True)


def select_base_directory() -> Path:
    """Abre un explorador para seleccionar directorio base."""
    root = tk.Tk()
    root.withdraw()  # Oculta ventana principal

    print("\n📂 Selecciona el directorio donde se creará el proyecto...\n")

    folder_selected = filedialog.askdirectory(title="Selecciona carpeta destino")

    if not folder_selected:
        raise SystemExit("❌ No seleccionaste ninguna carpeta. Cancelado.")

    return Path(folder_selected)


def create_skeleton(project_root: Path):
    """Crea la estructura completa dentro del root del proyecto."""
    print(f"\n📦 Generando skeleton en:\n   {project_root}\n")

    # --- Crear carpetas ---
    for folder in FOLDERS:
        path = project_root / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Folder: {folder}")

        # Si está dentro de src/, es paquete Python
        if folder.startswith("src/"):
            touch_init(path)

    # --- Crear archivos base ---
    for file, content in FILES.items():
        filepath = project_root / file
        filepath.parent.mkdir(parents=True, exist_ok=True)

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

    # 1. Pedir nombre del proyecto
    project_name = input("📌 Ingresa el nombre del proyecto: ").strip()

    if not project_name:
        raise SystemExit("❌ Nombre inválido. Cancelado.")

    # 2. Seleccionar directorio base con explorador
    base_dir = select_base_directory()

    # 3. Crear carpeta raíz del proyecto
    project_root = base_dir / project_name

    if project_root.exists():
        raise SystemExit(f"❌ La carpeta '{project_name}' ya existe en ese directorio.")

    project_root.mkdir()

    # 4. Generar skeleton dentro
    create_skeleton(project_root)
