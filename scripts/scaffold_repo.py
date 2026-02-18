from pathlib import Path

# ============================================================
# Skeleton oficial del proyecto (basado en tu treemap real)
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


def create_skeleton(root: Path):
    print(f"\n📦 Generando skeleton en: {root}\n")

    # --- Carpetas ---
    for folder in FOLDERS:
        path = root / folder
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Folder: {folder}")

        # Si está dentro de src/, es paquete Python
        if folder.startswith("src/"):
            touch_init(path)

    # --- Archivos ---
    for file, content in FILES.items():
        filepath = root / file
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
            print(f"📄 File created: {file}")
        else:
            print(f"⚠️ Already exists: {file}")

    print("\n🚀 Skeleton generado correctamente.\n")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    create_skeleton(Path.cwd())