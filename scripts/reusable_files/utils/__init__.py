"""
Utils - Utilidades modulares para ETL pipelines
"""

# Core utilities (siempre disponibles)
try:
    from .core.path_manager import PathManager
    from .core.config_loader import ConfigLoader
except ImportError:
    from utils.core.path_manager import PathManager
    from utils.core.config_loader import ConfigLoader

__all__ = ['PathManager', 'ConfigLoader']

# ETL utilities - Database
try:
    try:
        from .etl.database.sql_query_loader import SQLQueryLoader
        from .etl.database.duckdb_manager import DuckDBManager
    except ImportError:
        from utils.etl.database.sql_query_loader import SQLQueryLoader
        from utils.etl.database.duckdb_manager import DuckDBManager
    __all__.extend(['SQLQueryLoader', 'DuckDBManager'])
except ImportError:
    pass

# ETL utilities - Converters
try:
    try:
        from .etl.converters.excel_to_parquet import ExcelToParquet
        from .etl.converters.parquet_to_excel import ParquetToExcel
    except ImportError:
        from utils.etl.converters.excel_to_parquet import ExcelToParquet
        from utils.etl.converters.parquet_to_excel import ParquetToExcel
    __all__.extend(['ExcelToParquet', 'ParquetToExcel'])
except ImportError:
    pass

# ETL utilities - Validators
try:
    try:
        from .etl.validators.data_validator import DataValidator
    except ImportError:
        from utils.etl.validators.data_validator import DataValidator
    __all__.append('DataValidator')
except ImportError:
    pass

# Formatting utilities
try:
    try:
        from .formatting.excel_formatter import ExcelFormatter
    except ImportError:
        from utils.formatting.excel_formatter import ExcelFormatter
    __all__.append('ExcelFormatter')
except ImportError:
    pass

# UI utilities
try:
    try:
        from .ui.file_dialog_helper import FileDialogHelper
    except ImportError:
        from utils.ui.file_dialog_helper import FileDialogHelper
    __all__.append('FileDialogHelper')
except ImportError:
    pass

__version__ = '1.0.0'
