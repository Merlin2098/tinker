"""
DuckDBManager - Gestión centralizada de DuckDB
"""
import duckdb
import polars as pl
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DuckDBManager:
    """Gestiona conexiones y operaciones con DuckDB"""
    
    def __init__(self, database: str = ':memory:'):
        """
        Inicializa conexión a DuckDB
        
        Args:
            database: Ruta a la base de datos o ':memory:' para en memoria
        """
        self.database = database
        self.conn = duckdb.connect(database)
    
    def load_parquet(self, path: str, table_name: str = 'silver_data') -> int:
        """
        Carga archivo Parquet en una tabla
        
        Args:
            path: Ruta al archivo Parquet
            table_name: Nombre de la tabla a crear
        
        Returns:
            Número de filas cargadas
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Archivo Parquet no encontrado: {path}")
        
        # Crear tabla desde Parquet
        self.conn.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_parquet('{path}')
        """)
        
        # Obtener número de filas
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0]
    
    def load_excel(self, path: str, table_name: str = 'silver_data') -> int:
        """
        Carga archivo Excel en una tabla usando Polars
        
        Args:
            path: Ruta al archivo Excel
            table_name: Nombre de la tabla a crear
        
        Returns:
            Número de filas cargadas
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"Archivo Excel no encontrado: {path}")
        
        # Leer con Polars
        df = pl.read_excel(path)
        
        # Registrar en DuckDB
        self.conn.register(table_name, df)
        
        # Obtener número de filas
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0]
    
    def create_table_from_dict(self, data: Dict[str, Any], table_name: str) -> None:
        """
        Crea tabla desde diccionario (útil para schemas como Likert)
        
        Args:
            data: Diccionario con datos (key: valor)
            table_name: Nombre de la tabla a crear
        """
        # Convertir diccionario a lista de tuplas
        rows = [(key, value) for key, value in data.items()]
        
        # Eliminar tabla si existe
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Crear tabla
        self.conn.execute(f"""
            CREATE TABLE {table_name} (
                valor_texto VARCHAR,
                valor_numerico INTEGER
            )
        """)
        
        # Insertar datos
        self.conn.executemany(f"INSERT INTO {table_name} VALUES (?, ?)", rows)
    
    def execute_query(self, sql: str) -> Any:
        """
        Ejecuta query SQL y retorna result
        
        Args:
            sql: Query SQL a ejecutar
        
        Returns:
            Resultado de la query
        """
        return self.conn.execute(sql)
    
    def execute_query_to_df(self, sql: str) -> pl.DataFrame:
        """
        Ejecuta query y retorna DataFrame de Polars
        
        Args:
            sql: Query SQL a ejecutar
        
        Returns:
            DataFrame de Polars
        """
        return self.conn.execute(sql).pl()
    
    def fetch_one(self, sql: str) -> Optional[Tuple]:
        """
        Ejecuta query y retorna primera fila
        
        Args:
            sql: Query SQL a ejecutar
        
        Returns:
            Primera fila o None
        """
        result = self.conn.execute(sql).fetchone()
        return result
    
    def fetch_all(self, sql: str) -> List[Tuple]:
        """
        Ejecuta query y retorna todas las filas
        
        Args:
            sql: Query SQL a ejecutar
        
        Returns:
            Lista de tuplas
        """
        return self.conn.execute(sql).fetchall()
    
    def table_exists(self, table_name: str) -> bool:
        """
        Verifica si una tabla existe
        
        Args:
            table_name: Nombre de la tabla
        
        Returns:
            True si existe
        """
        result = self.conn.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        """).fetchone()
        
        return result[0] > 0
    
    def drop_table(self, table_name: str) -> None:
        """
        Elimina una tabla
        
        Args:
            table_name: Nombre de la tabla a eliminar
        """
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    
    def get_row_count(self, table_name: str) -> int:
        """
        Obtiene número de filas de una tabla
        
        Args:
            table_name: Nombre de la tabla
        
        Returns:
            Número de filas
        """
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0]
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Obtiene nombres de columnas de una tabla
        
        Args:
            table_name: Nombre de la tabla
        
        Returns:
            Lista de nombres de columnas
        """
        result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
        return [row[0] for row in result]
    
    def close(self) -> None:
        """Cierra la conexión a DuckDB"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()