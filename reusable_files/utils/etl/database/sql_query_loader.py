"""
SQLQueryLoader - Parser de archivos SQL con queries nombradas
"""
from pathlib import Path
from typing import Dict, List, Optional


class SQLQueryLoader:
    """
    Carga y parsea archivos SQL con queries nombradas.

    Formatos soportados:
    - -- query_name: <name>
    - -- @query: <name>
    """
    
    def __init__(self, sql_file: str):
        """
        Inicializa el loader
        
        Args:
            sql_file: Ruta al archivo SQL
        """
        self.sql_file = Path(sql_file)
        self.queries: Dict[str, str] = {}
        self._parse()
    
    def _parse(self):
        """Parsea el archivo SQL extrayendo queries nombradas"""
        if not self.sql_file.exists():
            raise FileNotFoundError(f"Archivo SQL no encontrado: {self.sql_file}")

        with open(self.sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        current_query_name = None
        current_query_lines = []

        for line in sql_content.split('\n'):
            # Detectar inicio de nueva query - acepta ambos formatos:
            # -- query_name: <name>
            # -- @query: <name>
            is_query_marker = False
            query_name = None

            if '-- query_name:' in line:
                is_query_marker = True
                query_name = line.split('query_name:')[1].strip()
            elif '-- @query:' in line:
                is_query_marker = True
                query_name = line.split('@query:')[1].strip()

            if is_query_marker:
                # Guardar query anterior si existe
                if current_query_name and current_query_lines:
                    self.queries[current_query_name] = '\n'.join(current_query_lines).strip()

                # Iniciar nueva query
                current_query_name = query_name
                current_query_lines = []

            # Agregar línea a query actual (ignorar otros comentarios)
            elif current_query_name is not None:
                if not line.strip().startswith('--'):
                    current_query_lines.append(line)

        # Guardar última query
        if current_query_name and current_query_lines:
            self.queries[current_query_name] = '\n'.join(current_query_lines).strip()
    
    def get_query(self, name: str) -> str:
        """
        Obtiene una query por nombre
        
        Args:
            name: Nombre de la query
        
        Returns:
            Query SQL
        
        Raises:
            KeyError: Si la query no existe
        """
        if name not in self.queries:
            raise KeyError(f"Query '{name}' no encontrada. Disponibles: {self.list_queries()}")
        
        return self.queries[name]
    
    def list_queries(self) -> List[str]:
        """
        Lista nombres de queries disponibles
        
        Returns:
            Lista de nombres
        """
        return list(self.queries.keys())
    
    def has_query(self, name: str) -> bool:
        """
        Verifica si existe una query
        
        Args:
            name: Nombre de la query
        
        Returns:
            True si existe
        """
        return name in self.queries
    
    def get_all_queries(self) -> Dict[str, str]:
        """
        Obtiene todas las queries
        
        Returns:
            Diccionario con todas las queries
        """
        return self.queries.copy()