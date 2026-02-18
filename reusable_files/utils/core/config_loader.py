"""
ConfigLoader - Carga centralizada de archivos de configuración
"""
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigLoader:
    """Carga y gestiona archivos de configuración YAML y JSON"""
    
    def __init__(self, config_path: str):
        """
        Inicializa el loader
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """Carga el archivo según su extensión"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")
        
        if self.config_path.suffix in ['.yaml', '.yml']:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        elif self.config_path.suffix == '.json':
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            raise ValueError(f"Formato no soportado: {self.config_path.suffix}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene valor usando notación de punto o directa
        
        Args:
            key_path: Clave con puntos (ej: 'pipeline.output.formats') o directa ('output.formats')
            default: Valor por defecto si no existe
        
        Returns:
            Valor encontrado o default
        """
        # Intentar primero con la ruta completa
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                # Si falla, intentar sin el primer nivel (para manejar inconsistencias)
                if len(keys) > 1:
                    alt_keys = keys[1:]
                    alt_value = self.config
                    try:
                        for alt_key in alt_keys:
                            alt_value = alt_value[alt_key]
                        return alt_value
                    except (KeyError, TypeError):
                        pass
                
                return default
        
        return value
    
    def get_input_config(self) -> Dict[str, Any]:
        """Obtiene configuración de input (maneja inconsistencias)"""
        # Intentar 'pipeline.input' primero
        input_config = self.get('pipeline.input')
        if input_config:
            return input_config
        
        # Intentar 'input' directo
        input_config = self.get('input')
        if input_config:
            return input_config
        
        return {}
    
    def get_output_config(self) -> Dict[str, Any]:
        """Obtiene configuración de output (maneja inconsistencias)"""
        # Intentar 'pipeline.output' primero
        output_config = self.get('pipeline.output')
        if output_config:
            return output_config
        
        # Intentar 'output' directo
        output_config = self.get('output')
        if output_config:
            return output_config
        
        return {}
    
    def get_formats(self) -> List[str]:
        """Obtiene lista de formatos de output"""
        output = self.get_output_config()
        return output.get('formats', [])
    
    def get_parquet_config(self) -> Dict[str, Any]:
        """Obtiene configuración específica de Parquet"""
        output = self.get_output_config()
        return output.get('parquet', {})
    
    def get_excel_config(self) -> Dict[str, Any]:
        """Obtiene configuración específica de Excel"""
        output = self.get_output_config()
        return output.get('excel', {})
    
    def get_sql_file(self) -> Optional[str]:
        """Obtiene ruta al archivo SQL de queries"""
        sql_config = self.get('pipeline.sql')
        if sql_config:
            return sql_config.get('queries_file')
        return None
    
    def get_columns_mapping(self) -> Dict[str, str]:
        """Obtiene mapeo de columnas"""
        # Intentar 'columns_mapping' directo
        mapping = self.get('columns_mapping')
        if mapping:
            return mapping
        
        # Intentar 'pipeline.columns.mapping'
        mapping = self.get('pipeline.columns.mapping')
        if mapping:
            return mapping
        
        return {}
    
    def get_date_columns(self) -> List[str]:
        """Obtiene lista de columnas de fecha"""
        # Intentar 'processing.date_columns'
        date_cols = self.get('processing.date_columns')
        if date_cols:
            return date_cols
        
        # Intentar 'pipeline.transformations.date_format.columns_to_format'
        date_cols = self.get('pipeline.transformations.date_format.columns_to_format')
        if date_cols:
            return date_cols
        
        return []
    
    def validate_required_keys(self, required_keys: List[str]) -> bool:
        """
        Valida que existan claves requeridas
        
        Args:
            required_keys: Lista de claves requeridas (notación punto)
        
        Returns:
            True si todas existen, False si falta alguna
        """
        for key in required_keys:
            if self.get(key) is None:
                return False
        return True
    
    @staticmethod
    def load_json(json_path: str, key: Optional[str] = None) -> Any:
        """
        Carga archivo JSON directamente
        
        Args:
            json_path: Ruta al archivo JSON
            key: Clave opcional a extraer del JSON
        
        Returns:
            Contenido del JSON o valor de la clave
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if key:
            return data.get(key)
        return data