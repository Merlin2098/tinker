"""
ParquetToExcel - Exportación de Parquet/DuckDB a Excel formateado
"""
import polars as pl
from pathlib import Path
from typing import Dict, Any, Optional


class ParquetToExcel:
    """Exporta datos a Excel con formato usando Polars"""
    
    def __init__(self):
        """Inicializa el exportador"""
        self.df: Optional[pl.DataFrame] = None
    
    def load_from_duckdb(self, duckdb_conn, query: str = "SELECT * FROM gold_data"):
        """
        Carga datos desde DuckDB
        
        Args:
            duckdb_conn: Conexión a DuckDB
            query: Query SQL a ejecutar
        """
        self.df = duckdb_conn.execute(query).pl()
    
    def load_from_parquet(self, parquet_path: str):
        """
        Carga datos desde archivo Parquet
        
        Args:
            parquet_path: Ruta al archivo Parquet
        """
        self.df = pl.read_parquet(parquet_path)
    
    def write_excel(
        self,
        output_path: str,
        sheet_name: str = "datos_gold",
        autofit: bool = True,
        freeze_panes: bool = True,
        autofilter: bool = True,
        table_style: Optional[str] = "Table Style Medium 2",
        float_precision: int = 2
    ) -> bool:
        """
        Escribe DataFrame a Excel con formato
        
        Args:
            output_path: Ruta de salida
            sheet_name: Nombre de la hoja
            autofit: Ajustar ancho de columnas
            freeze_panes: Congelar primera fila
            autofilter: Habilitar autofiltro
            table_style: Estilo de tabla (None para sin estilo)
            float_precision: Precisión de decimales
        
        Returns:
            True si éxito
        """
        if self.df is None:
            print("❌ No hay datos cargados")
            return False
        
        try:
            # Preparar opciones
            kwargs = {
                'worksheet': sheet_name,
                'autofit': autofit,
                'float_precision': float_precision
            }
            
            # Freeze panes
            if freeze_panes:
                kwargs['freeze_panes'] = (1, 0)
            
            # Autofilter
            if autofilter:
                kwargs['autofilter'] = True
            
            # Table style
            if table_style:
                kwargs['table_style'] = table_style
            
            # Escribir
            self.df.write_excel(output_path, **kwargs)
            
            return True
        
        except Exception as e:
            print(f"❌ Error al escribir Excel: {e}")
            return False
    
    def write_excel_from_config(self, output_path: str, config: Dict[str, Any]) -> bool:
        """
        Escribe Excel usando configuración
        
        Args:
            output_path: Ruta de salida
            config: Diccionario con configuración de Excel
        
        Returns:
            True si éxito
        """
        sheet_name = config.get('sheet_name', 'datos_gold')
        freeze_panes = config.get('freeze_panes', True)
        autofilter = config.get('auto_filter', True)
        
        return self.write_excel(
            output_path=output_path,
            sheet_name=sheet_name,
            freeze_panes=freeze_panes,
            autofilter=autofilter
        )