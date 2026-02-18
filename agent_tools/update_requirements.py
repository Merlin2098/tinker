import subprocess
import sys
import os
import io

# Forzamos que la salida estándar use UTF-8 para evitar errores de codificación con emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_update():
    # Usamos sys.executable para asegurar que usamos el Python del venv
    pip_command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    
    print("--- Actualizando dependencias desde requirements.txt ---")
    
    try:
        # Ejecutamos pip install
        # check=True lanzará una excepción si el comando falla
        subprocess.run(
            pip_command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        print("[OK] Entorno virtual actualizado correctamente.")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] No se pudieron instalar las dependencias:")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ocurrio un error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificamos si existe el archivo en la raíz (donde se ejecuta el git commit)
    if os.path.exists("requirements.txt"):
        run_update()
    else:
        print("[INFO] No se encontro requirements.txt. Saltando actualizacion.")