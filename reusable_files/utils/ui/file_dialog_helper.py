"""
FileDialogHelper - Diálogos de selección de archivos unificados
"""
import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple


class FileDialogHelper:
    """Helper para selección de archivos con tkinter + fallback CLI"""
    
    @staticmethod
    def select_file(
        title: str = "Seleccionar archivo",
        filetypes: Optional[List[Tuple[str, str]]] = None,
        initial_dir: Optional[str] = None,
        fallback_cli: bool = True
    ) -> Optional[Path]:
        """
        Abre diálogo de selección de archivo
        
        Args:
            title: Título del diálogo
            filetypes: Lista de tuplas (descripción, extensiones)
                      Ejemplo: [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
            initial_dir: Directorio inicial
            fallback_cli: Si True, busca en sys.argv si no hay GUI
        
        Returns:
            Path al archivo seleccionado o None
        """
        # 1. Verificar si se pasó como argumento CLI
        if fallback_cli and len(sys.argv) > 1:
            file_path = Path(sys.argv[1])
            if file_path.exists():
                return file_path
            else:
                print(f"⚠️  Archivo especificado no existe: {file_path}")
                return None
        
        # 2. Intentar usar tkinter
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Preparar tipos de archivo
            if filetypes is None:
                filetypes = [("All files", "*.*")]
            
            # Preparar directorio inicial
            if initial_dir is None:
                initial_dir = os.getcwd()
            
            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=filetypes,
                initialdir=initial_dir
            )
            
            root.destroy()
            
            if file_path:
                return Path(file_path)
            else:
                return None
        
        except ImportError:
            print("⚠️  GUI no disponible. Proporciona la ruta del archivo como argumento.")
            print(f"    Uso: python script.py <ruta_archivo>")
            return None
    
    @staticmethod
    def select_excel_file(title: str = "Seleccionar archivo Excel") -> Optional[Path]:
        """
        Selecciona archivo Excel
        
        Args:
            title: Título del diálogo
        
        Returns:
            Path al archivo o None
        """
        return FileDialogHelper.select_file(
            title=title,
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
    
    @staticmethod
    def select_parquet_file(title: str = "Seleccionar archivo Parquet") -> Optional[Path]:
        """
        Selecciona archivo Parquet
        
        Args:
            title: Título del diálogo
        
        Returns:
            Path al archivo o None
        """
        return FileDialogHelper.select_file(
            title=title,
            filetypes=[
                ("Parquet files", "*.parquet"),
                ("All files", "*.*")
            ]
        )
    
    @staticmethod
    def select_silver_file(title: str = "Seleccionar archivo Silver") -> Optional[Path]:
        """
        Selecciona archivo Silver (Parquet o Excel)
        
        Args:
            title: Título del diálogo
        
        Returns:
            Path al archivo o None
        """
        return FileDialogHelper.select_file(
            title=title,
            filetypes=[
                ("Parquet files", "*.parquet"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
    
    @staticmethod
    def validate_file_exists(file_path: Optional[Path]) -> bool:
        """
        Valida que el archivo exista
        
        Args:
            file_path: Path al archivo
        
        Returns:
            True si existe, False si no
        """
        if file_path is None:
            print("❌ No se seleccionó ningún archivo")
            return False
        
        if not file_path.exists():
            print(f"❌ El archivo no existe: {file_path}")
            return False
        
        return True