# Instrucciones Dummies (para ninos de 10 anos)

Esta guia te ensena a usar el framework sin complicarte.

## 0. Leer reglas base (obligatorio)

Escribe este comando en el chat del agente:

`Read .clinerules and agent/rules/agent_rules.md`

## 1. Activar el Kernel (obligatorio)

Activa el perfil que quieres (elige segun tu consola):

- Si no sabes cual elegir, mira: `instructions/model_agnostic/kernel_profiles.md`

- LITE:
  - PowerShell/CMD: `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile LITE`
  - Bash (Git Bash): `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile LITE`
  - Wrapper: `instructions/model_agnostic/activate_kernel.cmd LITE` o `./instructions/model_agnostic/activate_kernel.sh LITE`
- STANDARD:
  - PowerShell/CMD: `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile STANDARD`
  - Bash (Git Bash): `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile STANDARD`
  - Wrapper: `instructions/model_agnostic/activate_kernel.cmd STANDARD` o `./instructions/model_agnostic/activate_kernel.sh STANDARD`
- FULL:
  - PowerShell/CMD: `.\.venv\Scripts\python.exe agent_tools\activate_kernel.py --profile FULL`
  - Bash (Git Bash): `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe agent_tools/activate_kernel.py --profile FULL`
  - Wrapper: `instructions/model_agnostic/activate_kernel.cmd FULL` o `./instructions/model_agnostic/activate_kernel.sh FULL`

## 2. Archivos que vas a usar

- Plantilla oficial (ingles): `agent/user_task.yaml`
- Plantilla explicada (espanol dummies): `agent/task_templates/user_task_dummies_es.yaml`

## 3. Que significa cada parametro (facil)

1. `role`
- Es "quien trabaja".
- Opciones: `senior`, `executor`, `inspector`, `junior`.

2. `mode`
- Es "como trabaja".
- Opciones:
  - `ANALYZE_ONLY`: solo mira y explica.
  - `ANALYZE_AND_IMPLEMENT`: mira y luego cambia.
  - `IMPLEMENT_ONLY`: cambia directo.

2.1 `mode_profile`
- Es el perfil del kernel.
- Opciones: `LITE`, `STANDARD`, `FULL`.

3. `objective`
- Es la mision principal.
- Escribe aqui que quieres en palabras claras.

4. `files`
- Lista de archivos o carpetas que el agente puede tocar/revisar.
- Debe tener minimo 1 ruta.

5. `config.sources`
- Son "fuentes de ayuda" para la tarea.
- Cada fuente tiene:
  - `id`: nombre corto.
  - `path`: donde esta el archivo.
  - `purpose`: para que sirve.

6. `constraints`
- Reglas que el agente no debe romper.
- Ejemplo: "no cambies archivos fuera de la lista".

7. `risk_tolerance`
- Cuanto riesgo aceptas.
- Opciones: `LOW`, `MEDIUM`, `HIGH`.

8. `phase`
- En que etapa estas.
- Opciones:
  - `A_CONTRACT_VALIDATION` (validar contrato).
  - `B_EXECUTION` (ejecutar).

9. `validation`
- Estado de validacion del contrato.
- `status` opciones: `PENDING`, `PASSED`, `FAILED`.
- Si usas `phase: B_EXECUTION`, entonces:
  - `status` debe ser `PASSED`.
  - `validated_by` no puede ser null.
  - `validated_at` no puede ser null.

## 4. Regla de oro

Siempre haz esto:
1. Primero `A_CONTRACT_VALIDATION`.
2. Despues `B_EXECUTION` (solo si ya paso validacion).

## 4.1 Como pasar de Phase A a Phase B (paso a paso)

1. Ejecuta Phase A con `phase: A_CONTRACT_VALIDATION`.
2. Si el veredicto es PASSED, edita `agent/user_task.yaml` y cambia:
   - `phase: B_EXECUTION`
   - `validation.status: PASSED`
   - `validation.validated_by: <quien valido>` (ejemplo: tu nombre)
   - `validation.validated_at: <fecha ISO-8601>` (ejemplo: `2026-02-12T00:00:00Z`)
3. Vuelve a ejecutar el trigger para que el sistema lea el YAML actualizado.

## 4.2 Instruccion EXACTA del trigger

Escribe literalmente esta linea:
`Run task from agent/user_task.yaml`

Puedes escribirla en la misma conversacion despues de editar el YAML.
Si tu runner no re-lee automaticamente, vuelve a lanzar el comando/accion que use ese trigger.

## 5. Como pedir bien

Buenas instrucciones:
- "Revisa este archivo y dime que errores tiene."
- "Arregla solo esta funcion."
- "No cambies otros archivos."

Instrucciones malas:
- "Arregla todo."
- "Haz lo que quieras."

## 6. Skills utiles

- `debugger_orchestrator`: para investigar errores.
- `regression_test_automation`: para evitar que el error vuelva.
- `code_analysis_qa_gate`: para revisar calidad antes de cerrar.

