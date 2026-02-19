"""
Script to compile KPIS_Talent ETL Pipeline with PyInstaller (PySide6 + modular architecture).
Usage: python generar_exe.py
Must be run from an activated virtual environment (.venv).
"""

import PyInstaller.__main__
import shutil
import sys
from pathlib import Path


APP_NAME = "KPIS_Talent"


def is_venv():
    """Check if the script is running inside a virtual environment."""
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
    )


def confirm_execution():
    """Ask user confirmation before running the build."""
    print("\n" + "=" * 70)
    print("  BUILD CONFIRMATION")
    print("=" * 70)
    print("\nThis script will compile the application with PyInstaller.")
    print("\nActions:")
    print("  - Clean folders: dist/, build/, spec/")
    print("  - Compile application (may take 2-5 minutes)")
    print(f"  - Generate executable in: dist/{APP_NAME}/")
    print("\n" + "=" * 70)

    while True:
        response = input("\nProceed? (y/n): ").strip().lower()
        if response in ['y', 'yes', 's', 'si']:
            return True
        elif response in ['n', 'no']:
            print("\nBuild cancelled by user.")
            return False
        else:
            print("Invalid response. Enter 'y' or 'n'.")


def verify_data_files(project_root):
    """Verify that all required data files exist before building."""
    print("\nVerifying data files...")
    missing = []

    # Config directories and key files that must exist
    required_paths = [
        project_root / "config" / "yaml",
        project_root / "config" / "json",
        project_root / "config" / "queries",
        project_root / "config" / "esquemas",
        project_root / "config" / "themes",
        project_root / "config" / "resources" / "app.ico",
        project_root / "orchestrator" / "pipeline_config.yaml",
    ]

    for path in required_paths:
        if path.exists():
            print(f"  OK  {path.relative_to(project_root)}")
        else:
            missing.append(path.relative_to(project_root))
            print(f"  MISSING  {path.relative_to(project_root)}")

    if missing:
        print(f"\nERROR: {len(missing)} required path(s) missing.")
        return False

    print("All data files verified.")
    return True


def build_exe():
    """Compile the application using PyInstaller."""

    project_root = Path(__file__).parent

    # Verify data files
    if not verify_data_files(project_root):
        return False

    # Create spec directory
    spec_dir = project_root / "spec"
    spec_dir.mkdir(exist_ok=True)

    # Clean previous builds
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    spec_file = spec_dir / f"{APP_NAME}.spec"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("Previous dist/ removed")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("Previous build/ removed")

    if spec_file.exists():
        spec_file.unlink()
        print("Previous .spec removed")

    print("\n" + "=" * 70)
    print(f"  COMPILING {APP_NAME} WITH PYINSTALLER")
    print("=" * 70 + "\n")

    print("Configuration:")
    print("   Framework: PySide6")
    print("   Architecture: Modular (etl_*, orchestrator/, ui/, utils/)")
    print("   Mode: --onedir")
    print("   Window: --windowed (no console)")
    print(f"   Spec file: {spec_file}")
    print("")

    # Resolve paths for --add-data
    config_dir = project_root / "config"
    app_icon = config_dir / "resources" / "app.ico"
    yaml_dir = config_dir / "yaml"
    json_dir = config_dir / "json"
    queries_dir = config_dir / "queries"
    esquemas_dir = config_dir / "esquemas"
    themes_dir = config_dir / "themes"
    resources_dir = config_dir / "resources"
    pipeline_config = project_root / "orchestrator" / "pipeline_config.yaml"

    # Build PyInstaller arguments
    pyinstaller_args = [
        'main.py',                                  # Entrypoint
        f'--name={APP_NAME}',                       # Executable name
        '--onedir',                                  # Directory mode
        '--windowed',                                # No console window
        f'--icon={app_icon}',                        # Application icon
        f'--specpath={spec_dir}',                    # Spec file location

        # ===== DATA FILES =====
        # Config subdirectories (bundled into _internal/config/)
        f'--add-data={yaml_dir};config/yaml',
        f'--add-data={json_dir};config/json',
        f'--add-data={queries_dir};config/queries',
        f'--add-data={esquemas_dir};config/esquemas',
        f'--add-data={themes_dir};config/themes',
        f'--add-data={resources_dir};config/resources',
        # Orchestrator config
        f'--add-data={pipeline_config};orchestrator',

        # ===== HIDDEN IMPORTS - EXTERNAL LIBRARIES =====
        '--hidden-import=polars',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=openpyxl',
        '--hidden-import=openpyxl.cell',
        '--hidden-import=openpyxl.cell._writer',
        '--hidden-import=openpyxl.worksheet',
        '--hidden-import=openpyxl.worksheet._writer',
        '--hidden-import=xlsxwriter',
        '--hidden-import=fastexcel',
        '--hidden-import=duckdb',
        '--hidden-import=pyarrow',
        '--hidden-import=pyarrow.parquet',
        '--hidden-import=pydantic',
        '--hidden-import=dateutil',
        '--hidden-import=yaml',
        '--hidden-import=PyYAML',

        # ===== HIDDEN IMPORTS - PYSIDE6 =====
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',

        # ===== HIDDEN IMPORTS - ETL CORE =====
        '--hidden-import=etl_core',
        '--hidden-import=etl_core.step1',
        '--hidden-import=etl_core.step2',

        # ===== HIDDEN IMPORTS - ETL FORMS =====
        '--hidden-import=etl_forms',
        '--hidden-import=etl_forms.step1_forms',
        '--hidden-import=etl_forms.step2_forms',

        # ===== HIDDEN IMPORTS - ETL ITA SUBORDINATES =====
        '--hidden-import=etl_ita_subordinates',
        '--hidden-import=etl_ita_subordinates.step1_ita',
        '--hidden-import=etl_ita_subordinates.step1_managers',
        '--hidden-import=etl_ita_subordinates.step2_ita',

        # ===== HIDDEN IMPORTS - ETL MANDATORY COURSES =====
        '--hidden-import=etl_mandatorycourses',
        '--hidden-import=etl_mandatorycourses.step1_cursos_mandatorios',
        '--hidden-import=etl_mandatorycourses.step2_cursos_mandatorios',

        # ===== HIDDEN IMPORTS - ETL PSICO =====
        '--hidden-import=etl_psico',
        '--hidden-import=etl_psico.step1_psico',
        '--hidden-import=etl_psico.step2_psico',

        # ===== HIDDEN IMPORTS - ORCHESTRATOR =====
        '--hidden-import=orchestrator',
        '--hidden-import=orchestrator.pipeline',
        '--hidden-import=orchestrator.runner',
        '--hidden-import=orchestrator.contracts',
        '--hidden-import=orchestrator.config_builder',
        '--hidden-import=orchestrator.wrappers',
        '--hidden-import=orchestrator.wrappers.run_step2_ita',

        # ===== HIDDEN IMPORTS - UI =====
        '--hidden-import=ui',
        '--hidden-import=ui.main_window',
        '--hidden-import=ui.splash_screen',
        '--hidden-import=ui.widgets',
        '--hidden-import=ui.widgets.monitoring_panel',
        '--hidden-import=ui.widgets.console_widget',
        '--hidden-import=ui.widgets.author_info_widget',
        '--hidden-import=ui.widgets.file_selector_panel',
        '--hidden-import=ui.workers',
        '--hidden-import=ui.workers.pipeline_worker',

        # ===== HIDDEN IMPORTS - UTILS =====
        '--hidden-import=utils',
        '--hidden-import=utils.logger',
        '--hidden-import=utils.core',
        '--hidden-import=utils.core.config_loader',
        '--hidden-import=utils.core.path_manager',
        '--hidden-import=utils.etl',
        '--hidden-import=utils.etl.converters',
        '--hidden-import=utils.etl.converters.excel_to_parquet',
        '--hidden-import=utils.etl.converters.parquet_to_excel',
        '--hidden-import=utils.etl.database',
        '--hidden-import=utils.etl.database.duckdb_manager',
        '--hidden-import=utils.etl.database.sql_query_loader',
        '--hidden-import=utils.etl.validators',
        '--hidden-import=utils.etl.validators.data_validator',
        '--hidden-import=utils.formatting',
        '--hidden-import=utils.formatting.excel_formatter',
        '--hidden-import=utils.ui',
        '--hidden-import=utils.ui.file_dialog_helper',
        '--hidden-import=utils.ui.path_cache_manager',
        '--hidden-import=utils.ui.theme_manager',

        # ===== BUILD OPTIONS =====
        '--clean',
        '--noconfirm',
        '--noupx',
        '--optimize=2',
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

    print("\n" + "=" * 70)
    print("  BUILD COMPLETED")
    print("=" * 70)
    print(f"\nExecutable location: {dist_dir / APP_NAME}")

    print(f"\nGenerated structure:")
    print(f"  dist/")
    print(f"    {APP_NAME}/")
    print(f"          {APP_NAME}.exe        <- Main executable")
    print(f"          _internal/             <- Runtime (Python, DLLs, libs)")
    print(f"              config/            <- Configuration files")
    print(f"                  yaml/          <- ETL step configs")
    print(f"                  json/          <- Schemas, cache")
    print(f"                  queries/       <- SQL queries")
    print(f"                  esquemas/      <- JSON schemas")
    print(f"                  themes/        <- UI themes")
    print(f"                  resources/     <- Icons")
    print(f"              orchestrator/      <- Pipeline config")

    print(f"\nDistribution:")
    print(f"   1. Compress the entire '{APP_NAME}' folder into a ZIP")
    print(f"   2. Distribute the ZIP file")
    print(f"   3. End users must:")
    print(f"      - Extract the ZIP to a permanent location")
    print(f"      - Run {APP_NAME}.exe")
    print(f"      - Do NOT move the .exe outside its folder")

    print(f"\nTarget system requirements:")
    print(f"   - Windows 10/11 (64-bit)")
    print(f"   - 4 GB RAM minimum recommended")

    print("\n" + "=" * 70 + "\n")

    # Verify the executable was created
    exe_path = dist_dir / APP_NAME / f"{APP_NAME}.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Verification OK: {exe_path}")
        print(f"Executable size: {size_mb:.2f} MB")
    else:
        print(f"ERROR: Executable not found at {exe_path}")
        return False

    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(f"  {APP_NAME} - EXECUTABLE GENERATOR")
    print("=" * 70)

    # Validate virtual environment
    if not is_venv():
        print("\nERROR: No virtual environment detected.")
        print("\nThis script must run inside a virtual environment.")
        print("\nTo activate the venv:")
        print("   .venv\\Scripts\\activate")
        print("\n" + "=" * 70 + "\n")
        sys.exit(1)

    print(f"\nVirtual environment detected")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Location: {sys.prefix}")

    # Confirm with user
    if not confirm_execution():
        sys.exit(0)

    # Run build
    try:
        success = build_exe()
        if success:
            print("\nBuild completed successfully!")
            print(f"\nNext steps:")
            print(f"   1. Test the executable in: dist/{APP_NAME}/")
            print(f"   2. Compress the folder into ZIP")
            print(f"   3. Distribute the ZIP file\n")
        else:
            print("\nBuild failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nBuild error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
