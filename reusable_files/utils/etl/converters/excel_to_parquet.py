"""
ExcelToParquet - Conversión de Excel a Parquet usando openpyxl
"""
import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class ExcelToParquet:
    """Convierte archivos Excel a Parquet con transformaciones"""
    
    def __init__(self, excel_path: str, config: Dict[str, Any]):
        """
        Inicializa el conversor
        
        Args:
            excel_path: Ruta al archivo Excel
            config: Diccionario de configuración
        """
        self.excel_path = Path(excel_path)
        self.config = config
        self.data: List[Dict[str, Any]] = []
        self.headers: List[str] = []
        self.stats = {
            'original_rows': 0,
            'final_rows': 0,
            'columns_count': 0,
            'rows_skipped': 0
        }

    def _get_sheet_name(self) -> Optional[str]:
        input_cfg = self.config.get("input", {}) or {}
        io_cfg = self.config.get("io", {}) or {}
        sheet_name = input_cfg.get("sheet_name")
        if sheet_name in (None, ""):
            sheet_name = io_cfg.get("sheet_name")
        if sheet_name in (None, ""):
            return None
        return str(sheet_name)

    def _get_header_row(self) -> int:
        input_cfg = self.config.get("input", {}) or {}
        io_cfg = self.config.get("io", {}) or {}

        header_row = input_cfg.get("header_row", None)
        if header_row is None:
            header_row = io_cfg.get("header_row", 1)

        try:
            header_row_int = int(header_row)
        except (TypeError, ValueError):
            header_row_int = 1

        # openpyxl is 1-based; allow configs that specify 0-based row=0 for first row
        if header_row_int <= 0:
            return 1
        return header_row_int
    
    def _parse_date(self, date_value: Any) -> Optional[str]:
        """
        Convierte fecha a formato YYYY-MM-DD
        
        Args:
            date_value: Valor de fecha
        
        Returns:
            Fecha en formato YYYY-MM-DD o None
        """
        if date_value is None or date_value == '':
            return None
        
        try:
            # Si ya es datetime
            if isinstance(date_value, datetime):
                return date_value.strftime('%Y-%m-%d')
            
            # Si es string, intentar parsear
            if isinstance(date_value, str):
                date_value = date_value.strip()
                
                formats = [
                    '%d/%m/%Y',  # 25/12/1990
                    '%d-%m-%Y',  # 25-12-1990
                    '%Y-%m-%d',  # 1990-12-25
                    '%Y/%m/%d',  # 1990/12/25
                    '%d.%m.%Y',  # 25.12.1990
                ]
                
                for fmt in formats:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            return None
        
        except Exception:
            return None
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """
        Convierte valor a float

        Args:
            value: Valor numérico

        Returns:
            Float o None
        """
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def load_excel(self) -> bool:
        """
        Carga datos desde Excel

        Returns:
            True si éxito
        """
        try:
            # Cargar workbook (read_only para eficiencia)
            wb = openpyxl.load_workbook(self.excel_path, read_only=True, data_only=True)

            # Obtener nombre de hoja
            sheet_name = self._get_sheet_name()
            if sheet_name and sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
            else:
                # Default: use first sheet (not necessarily wb.active)
                ws = wb[wb.sheetnames[0]]

            # Obtener fila de encabezados
            header_row = self._get_header_row()

            # En algunos Excels la dimensión no está definida y read_only reporta max_row=1.
            # Si eso ocurre, recargar en modo normal para obtener dimensiones reales.
            if ws.max_row <= header_row or ws.max_column <= 1:
                wb.close()
                wb = openpyxl.load_workbook(self.excel_path, read_only=False, data_only=True)
                if sheet_name and sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                else:
                    ws = wb[wb.sheetnames[0]]

            # Leer encabezados
            all_headers = [cell.value for cell in ws[header_row]]

            # Obtener columnas a procesar
            columns_mapping = self.config.get('columns_mapping', {})

            if columns_mapping:
                # Usar mapeo específico
                required_columns = list(columns_mapping.keys())
                column_indices = {}

                for col_name in required_columns:
                    try:
                        idx = all_headers.index(col_name)
                        column_indices[col_name] = idx
                    except ValueError:
                        pass

                self.headers = list(columns_mapping.values())
            else:
                # Usar todas las columnas
                column_indices = {h: i for i, h in enumerate(all_headers) if h is not None}
                self.headers = [h for h in all_headers if h is not None]

            # Obtener columnas de fecha
            date_columns = self.config.get('processing', {}).get('date_columns', [])
            date_columns.extend(
                self.config.get('transformations', {}).get('date_format', {}).get('columns_to_format', [])
            )

            # Obtener columnas numéricas
            numeric_columns = self.config.get('processing', {}).get('numeric_columns', [])

            # Obtener prefijos de filas a descartar
            skip_row_prefixes = self.config.get('processing', {}).get('skip_row_prefixes', [])

            # Procesar filas
            rows_processed = 0
            rows_skipped = 0

            for row in ws.iter_rows(min_row=header_row + 1):
                first_col_idx = list(column_indices.values())[0] if column_indices else 0
                first_col_value = row[first_col_idx].value

                # Verificar si debe saltarse fila vacía
                if self.config.get('processing', {}).get('drop_empty_first_column', False):
                    first_empty = first_col_value is None or str(first_col_value).strip() == ''
                    if first_empty:
                        has_other_values = False
                        for col_idx in column_indices.values():
                            if col_idx == first_col_idx:
                                continue
                            cell_value = row[col_idx].value
                            if cell_value is not None and str(cell_value).strip() != '':
                                has_other_values = True
                                break
                        if not has_other_values:
                            rows_skipped += 1
                            continue

                # Verificar si la primera columna empieza con un prefijo a descartar
                if skip_row_prefixes and first_col_value is not None:
                    first_col_str = str(first_col_value).strip().lower()
                    if any(first_col_str.startswith(prefix.lower()) for prefix in skip_row_prefixes):
                        rows_skipped += 1
                        continue

                # Construir registro
                record = {}

                if columns_mapping:
                    # Con mapeo
                    for orig_name, new_name in columns_mapping.items():
                        if orig_name in column_indices:
                            col_idx = column_indices[orig_name]
                            cell_value = row[col_idx].value

                            # Procesar según tipo
                            if orig_name in date_columns:
                                record[new_name] = self._parse_date(cell_value)
                            elif orig_name in numeric_columns:
                                record[new_name] = self._parse_numeric(cell_value)
                            else:
                                record[new_name] = str(cell_value) if cell_value is not None else None
                else:
                    # Sin mapeo
                    for col_name, col_idx in column_indices.items():
                        cell_value = row[col_idx].value

                        if col_name in date_columns:
                            record[col_name] = self._parse_date(cell_value)
                        elif col_name in numeric_columns:
                            record[col_name] = self._parse_numeric(cell_value)
                        else:
                            record[col_name] = str(cell_value) if cell_value is not None else None
                
                self.data.append(record)
                rows_processed += 1
            
            wb.close()
            
            self.stats['original_rows'] = rows_processed + rows_skipped
            self.stats['final_rows'] = rows_processed
            self.stats['rows_skipped'] = rows_skipped
            self.stats['columns_count'] = len(self.headers)
            
            return True
        
        except Exception as e:
            print(f"❌ Error al cargar Excel: {e}")
            return False
    
    def save_parquet(self, output_path: str, compression: str = 'snappy') -> bool:
        """
        Guarda datos en formato Parquet
        
        Args:
            output_path: Ruta de salida
            compression: Tipo de compresión
        
        Returns:
            True si éxito
        """
        try:
            # Preparar datos por columna
            numeric_columns = self.config.get('processing', {}).get('numeric_columns', [])
            arrays = {}
            for col in self.headers:
                col_data = [row.get(col) for row in self.data]
                if col in numeric_columns:
                    arrays[col] = pa.array(col_data, type=pa.float64())
                else:
                    arrays[col] = pa.array(col_data, type=pa.string())
            
            # Crear tabla PyArrow
            table = pa.table(arrays)
            
            # Escribir Parquet
            pq.write_table(table, output_path, compression=compression)
            
            return True
        
        except Exception as e:
            print(f"❌ Error al guardar Parquet: {e}")
            return False
    
    def save_excel(self, output_path: str) -> bool:
        """
        Guarda datos en formato Excel
        
        Args:
            output_path: Ruta de salida
        
        Returns:
            True si éxito
        """
        try:
            # Crear workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Datos Procesados"
            
            # Escribir encabezados
            for col_idx, header in enumerate(self.headers, start=1):
                ws.cell(row=1, column=col_idx, value=header)
            
            # Escribir datos
            for row_idx, record in enumerate(self.data, start=2):
                for col_idx, header in enumerate(self.headers, start=1):
                    value = record.get(header)
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            # Guardar
            wb.save(output_path)
            wb.close()
            
            return True
        
        except Exception as e:
            print(f"❌ Error al guardar Excel: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas del procesamiento"""
        return self.stats.copy()
