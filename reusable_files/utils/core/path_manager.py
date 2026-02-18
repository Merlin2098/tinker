"""
PathManager - Gestión centralizada de rutas y directorios
"""
import os
from pathlib import Path
from typing import Optional


class PathManager:
    """Gestiona resolución de paths y creación de directorios"""
    
    def __init__(self, script_path: Optional[str] = None):
        """
        Inicializa el PathManager
        
        Args:
            script_path: Ruta del script que llama (usar __file__)
        """
        self.script_path = Path(script_path).resolve() if script_path else None
        self.project_root = self._detect_project_root()
    
    def _detect_project_root(self) -> Path:
        """
        Detecta la raíz del proyecto usando marker files.
        Busca .gitignore, main.py, o requirements.txt subiendo por el árbol.
        """
        if self.script_path:
            current = self.script_path.parent

            # Marker files que indican la raíz del proyecto
            markers = ['.gitignore', 'main.py', 'requirements.txt', 'pyproject.toml']

            # Subir hasta encontrar un marker o llegar al límite (10 niveles)
            for _ in range(10):
                for marker in markers:
                    if (current / marker).exists():
                        return current

                # Si llegamos a la raíz del sistema, parar
                if current.parent == current:
                    break

                current = current.parent

            # Fallback 1: si hay carpeta 'src' en la ruta, usar su padre como raíz
            for parent in self.script_path.parents:
                if parent.name == "src":
                    return parent.parent

            # Fallback 2: asumir 3 niveles arriba (para src/core/people_point/ -> raíz)
            return self.script_path.parent.parent.parent
        else:
            # Usar directorio actual
            return Path.cwd()
    
    def resolve_config_path(self, filename: str, config_type: str = "yaml") -> Optional[Path]:
        """
        Busca archivo de configuración en múltiples ubicaciones
        
        Args:
            filename: Nombre del archivo (ej: 'forms_step1.yaml')
            config_type: Tipo de config ('yaml', 'json', 'sql')
        
        Returns:
            Path al archivo encontrado o None
        """
        # Carpeta según tipo
        folder_map = {
            'yaml': 'yaml',
            'json': 'json',
            'sql': 'sql'
        }
        
        config_folder = folder_map.get(config_type, config_type)
        
        # Ubicaciones a buscar
        locations = [
            # Opción 1: Desde raíz del proyecto en src/config/
            self.project_root / "src" / "config" / config_folder / filename,
            # Opción 2: Desde raíz del proyecto en config/
            self.project_root / "config" / config_folder / filename,
            # Opción 3: Desde directorio actual
            Path.cwd() / "config" / config_folder / filename,
            # Opción 4: Un nivel arriba
            Path.cwd().parent / "config" / config_folder / filename,
        ]
        
        for location in locations:
            if location.exists():
                return location.resolve()
        
        return None
    
    def get_output_dir(self, base_path: str, stage: str = 'silver') -> Path:
        """
        Determina directorio de salida según stage
        
        Args:
            base_path: Ruta base (puede ser path del archivo de entrada)
            stage: 'silver' o 'gold'
        
        Returns:
            Path al directorio de salida
        """
        base = Path(base_path)
        
        # Si es un archivo, obtener su directorio
        if base.is_file():
            base = base.parent
        
        # Manejar paths de solo lectura
        if str(base).startswith('/mnt/user-data/uploads'):
            base = Path('/mnt/user-data/outputs')
        
        # Si estamos en silver/, subir un nivel para crear gold/
        if base.name == 'silver' and stage == 'gold':
            base = base.parent
        
        # Crear directorio stage
        output_dir = base / stage
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    def handle_readonly_path(self, path: str) -> str:
        """
        Convierte paths de solo lectura a paths escribibles
        
        Args:
            path: Ruta original
        
        Returns:
            Ruta ajustada si es readonly, original si no
        """
        if path.startswith('/mnt/user-data/uploads'):
            return path.replace('/mnt/user-data/uploads', '/mnt/user-data/outputs')
        return path
    
    def resolve_sql_path(self, sql_file: str) -> Path:
        """
        Resuelve ruta a archivo SQL
        
        Args:
            sql_file: Ruta relativa o absoluta al archivo SQL
        
        Returns:
            Path resuelto
        """
        if os.path.isabs(sql_file):
            return Path(sql_file)
        
        # Separar por / y reconstruir
        parts = sql_file.replace('\\', '/').split('/')

        # Ubicaciones a buscar
        search_paths = [
            # Desde raíz del proyecto (path relativo completo)
            self.project_root / Path(*parts),
            # Desde src/config/sql/ si el path no incluye src/
            self.project_root / "src" / "config" / "sql" / Path(*parts) if not sql_file.startswith('src/') else None,
            # Desde directorio actual
            Path.cwd() / Path(*parts),
        ]

        for resolved in search_paths:
            if resolved and resolved.exists():
                return resolved

        raise FileNotFoundError(f"No se encuentra el archivo SQL: {sql_file}")
