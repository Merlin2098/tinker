"""
DataValidator - Validación de datos y esquemas
"""
from typing import Dict, List, Any, Tuple, Optional


class DataValidator:
    """Valida datos y esquemas"""
    
    @staticmethod
    def validate_required_columns(
        data_columns: List[str],
        required_columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Valida que existan columnas requeridas
        
        Args:
            data_columns: Columnas presentes en los datos
            required_columns: Columnas requeridas
        
        Returns:
            (éxito, columnas_faltantes)
        """
        missing = [col for col in required_columns if col not in data_columns]
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_likert_values(
        data: List[Dict[str, Any]],
        factor_columns: List[str],
        likert_schema: Dict[str, int]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Valida que valores de factores estén en schema Likert
        
        Args:
            data: Lista de registros
            factor_columns: Columnas que contienen factores
            likert_schema: Esquema Likert (texto -> número)
        
        Returns:
            (válido, valores_no_mapeados)
        """
        unmapped = []
        valid_values = set(likert_schema.keys())
        
        for factor_col in factor_columns:
            found_values = set()
            
            for record in data:
                value = record.get(factor_col)
                if value is not None and value not in valid_values:
                    found_values.add(value)
            
            if found_values:
                for value in found_values:
                    count = sum(1 for r in data if r.get(factor_col) == value)
                    unmapped.append({
                        'columna': factor_col,
                        'valor': value,
                        'cantidad': count
                    })
        
        return len(unmapped) == 0, unmapped
    
    @staticmethod
    def validate_date_format(
        data: List[Dict[str, Any]],
        date_columns: List[str],
        expected_format: str = "YYYY-MM-DD"
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Valida formato de fechas
        
        Args:
            data: Lista de registros
            date_columns: Columnas de fecha
            expected_format: Formato esperado
        
        Returns:
            (válido, fechas_inválidas)
        """
        from datetime import datetime
        
        invalid_dates = []
        
        for date_col in date_columns:
            for idx, record in enumerate(data):
                value = record.get(date_col)
                
                if value is None:
                    continue
                
                # Validar formato YYYY-MM-DD
                try:
                    datetime.strptime(str(value), '%Y-%m-%d')
                except ValueError:
                    invalid_dates.append({
                        'columna': date_col,
                        'fila': idx + 2,  # +2 porque Excel empieza en 1 y hay header
                        'valor': value
                    })
        
        return len(invalid_dates) == 0, invalid_dates
    
    @staticmethod
    def validate_no_nulls(
        data: List[Dict[str, Any]],
        columns: List[str]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Valida que columnas no tengan nulos
        
        Args:
            data: Lista de registros
            columns: Columnas a validar
        
        Returns:
            (válido, registros_con_nulos)
        """
        records_with_nulls = []
        
        for idx, record in enumerate(data):
            null_columns = []
            for col in columns:
                if record.get(col) is None or str(record.get(col)).strip() == '':
                    null_columns.append(col)
            
            if null_columns:
                records_with_nulls.append({
                    'fila': idx + 2,
                    'columnas_nulas': null_columns
                })
        
        return len(records_with_nulls) == 0, records_with_nulls
    
    @staticmethod
    def validate_numeric_range(
        data: List[Dict[str, Any]],
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Valida que valores numéricos estén en rango
        
        Args:
            data: Lista de registros
            column: Columna a validar
            min_value: Valor mínimo permitido
            max_value: Valor máximo permitido
        
        Returns:
            (válido, valores_fuera_rango)
        """
        out_of_range = []
        
        for idx, record in enumerate(data):
            value = record.get(column)
            
            if value is None:
                continue
            
            try:
                num_value = float(value)
                
                if min_value is not None and num_value < min_value:
                    out_of_range.append({
                        'fila': idx + 2,
                        'valor': num_value,
                        'error': f'Menor que mínimo ({min_value})'
                    })
                
                if max_value is not None and num_value > max_value:
                    out_of_range.append({
                        'fila': idx + 2,
                        'valor': num_value,
                        'error': f'Mayor que máximo ({max_value})'
                    })
            
            except ValueError:
                out_of_range.append({
                    'fila': idx + 2,
                    'valor': value,
                    'error': 'No es un número válido'
                })
        
        return len(out_of_range) == 0, out_of_range
    
    @staticmethod
    def print_validation_errors(errors: List[Dict[str, Any]], error_type: str):
        """
        Imprime errores de validación de forma legible
        
        Args:
            errors: Lista de errores
            error_type: Tipo de error
        """
        if not errors:
            return
        
        print(f"\n⚠️  {error_type}:")
        print("=" * 60)
        
        for error in errors[:10]:  # Mostrar máximo 10
            print(f"  • {error}")
        
        if len(errors) > 10:
            print(f"  ... y {len(errors) - 10} más")
        
        print("=" * 60)