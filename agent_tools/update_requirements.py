import subprocess
import sys
import os

def run_update():
    # Detectar el ejecutable de pip dentro del entorno virtual actual
    # sys.executable apunta al python.exe de tu .venv si el hook lo llama correctamente
    pip_executable = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    
    print(f"--- Actualizando dependencias desde requirements.txt ---")
    
    try:
        # Ejecutamos pip install
        result = subprocess.run(
            pip_executable, 
            capture_output=True, 
            text=True, 
            check=True
        )
        print("✅ Entorno virtual actualizado correctamente.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al actualizar las dependencias:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Solo ejecutamos si el archivo requirements.txt existe en la raíz
    if os.path.exists("requirements.txt"):
        run_update()
    else:
        print("⚠️ No se encontró requirements.txt en la raíz del proyecto.")