
import os
import sys
import yaml
import subprocess
from pathlib import Path
from agent_tools.wrappers.skill_builder_wrapper import run as run_builder

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "agent/skills"
WRAPPERS_DIR = REPO_ROOT / "agent_tools/wrappers"
COMPILER_SCRIPT = REPO_ROOT / "agent_tools/compile_registry.py"

def load_yaml(path: Path):
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run(args: dict) -> dict:
    """
    Executes the skill merge process: Build New -> Delete Old -> Recompile.
    """
    # 1. Extract Inputs
    skills_to_delete = args.get("skills_to_delete", [])
    force_core = args.get("force_core", False)
    
    if not skills_to_delete:
        return {"status": "error", "message": "No 'skills_to_delete' provided."}

    # 2. Safety Check: Verify permissions to delete
    meta_files = list(SKILLS_DIR.glob("**/*.meta.yaml"))
    meta_map = {} # name -> path
    
    for mf in meta_files:
        try:
            data = load_yaml(mf)
            if data and 'name' in data:
                meta_map[data['name']] = {
                    'path': mf,
                    'data': data
                }
        except:
            pass

    files_to_remove = []
    
    for skill in skills_to_delete:
        if skill not in meta_map:
             return {"status": "error", "message": f"Skill to delete not found: '{skill}'"}
        
        info = meta_map[skill]
        tier = info['data'].get("tier", "lazy")
        
        if tier == "core" and not force_core:
             return {"status": "error", "message": f"Cannot delete CORE skill '{skill}' without force_core=True."}
             
        # Identify files
        meta_path = info['path']
        md_path = meta_path.with_suffix('') # .md is .meta.yaml minus .meta.yaml plus .md... wait. 
        # Actually standard is name.meta.yaml -> name.md
        # pathlib with_suffix replaces the last suffix. .meta.yaml is two.
        # easier: parent / (name + ".md")
        md_path = meta_path.parent / f"{skill}.md"
        
        # Wrapper
        # We need to guess the wrapper path? Or check the .meta.yaml?
        # Usually agent_tools/wrappers/<name>_wrapper.py
        wrapper_path = WRAPPERS_DIR / f"{skill}_wrapper.py"
        
        files_to_remove.append(meta_path)
        if md_path.exists(): files_to_remove.append(md_path)
        if wrapper_path.exists(): files_to_remove.append(wrapper_path)

    # 3. Build the NEW skill
    # We pass the creation args to the skill_builder wrapper
    print(f"Building new skill: {args.get('skill_name')}")
    build_result = run_builder(args)
    
    if build_result.get("status") != "success":
        return {
            "status": "error", 
            "message": f"Failed to build new skill. Aborting merge. Error: {build_result.get('message')}"
        }

    # 4. Delete Old Files
    deleted_log = []
    try:
        print("Deleting obsolete skills...")
        for f in files_to_remove:
            if f.exists():
                os.remove(f)
                deleted_log.append(str(f))
                print(f"  - Deleted: {f}")
    except Exception as e:
        # Warning: Partial deletion possible. System might be in dirty state.
        # But compile_registry should handle missing files gracefully.
        return {
            "status": "warning",
            "message": f"New skill created, but failed to delete some old files: {str(e)}",
            "created": build_result.get("files_created"),
            "deleted": deleted_log
        }

    # 5. Recompile (Builder ran it, but we deleted files *after*, so run again)
    print("Re-compiling registry after deletion...")
    subprocess.run([sys.executable, str(COMPILER_SCRIPT)], capture_output=True)

    return {
        "status": "success",
        "message": "Merge complete.",
        "new_skill": args.get("skill_name"),
        "deleted_skills": skills_to_delete,
        "files_deleted_count": len(deleted_log)
    }
