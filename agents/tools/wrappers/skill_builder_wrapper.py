
import os
import sys
import yaml
import subprocess
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILLS_DIR = REPO_ROOT / "agents/logic/skills"
WRAPPERS_DIR = REPO_ROOT / "agents/tools/wrappers"
COMPILER_SCRIPT = REPO_ROOT / "agents/tools/compile_registry.py"

def save_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def run(args: dict) -> dict:
    """
    Executes the skill creation process.
    """
    skill_name = args.get("skill_name")
    cluster = args.get("cluster", "misc")
    description = args.get("description", "No description provided.")
    doc_md = args.get("doc_md")
    wrapper_code = args.get("wrapper_code")
    metadata_input = args.get("metadata", {})
    
    # 1. Validation
    if not skill_name or not skill_name.isidentifier():
        return {"status": "error", "message": f"Invalid skill_name: '{skill_name}'"}
    
    if not doc_md or not wrapper_code:
        return {"status": "error", "message": "Missing 'doc_md' or 'wrapper_code'."}

    # Target Paths
    target_skill_dir = SKILLS_DIR / cluster
    md_path = target_skill_dir / f"{skill_name}.md"
    meta_path = target_skill_dir / f"{skill_name}.meta.yaml"
    wrapper_path = WRAPPERS_DIR / f"{skill_name}_wrapper.py"
    
    if md_path.exists() or meta_path.exists() or wrapper_path.exists():
         return {"status": "error", "message": f"Skill '{skill_name}' already exists."}

    # 2. Prepare Metadata Content
    meta_content = {
        "name": skill_name,
        "tier": metadata_input.get("tier", "lazy"),
        "cluster": cluster,
        "priority": metadata_input.get("priority", 50),
        "purpose": description,
        "triggers": metadata_input.get("triggers", {})
    }
    
    # 3. Write Files
    try:
        print(f"Creating skill: {skill_name}")
        
        # Write .md
        save_file(md_path, doc_md)
        print(f"  - Written: {md_path}")
        
        # Write .meta.yaml
        with open(meta_path, 'w', encoding='utf-8') as f:
            yaml.dump(meta_content, f, sort_keys=False)
        print(f"  - Written: {meta_path}")
        
        # Write Wrapper
        save_file(wrapper_path, wrapper_code)
        print(f"  - Written: {wrapper_path}")
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to write files: {str(e)}"}

    # 4. Run Compiler
    try:
        print("Running registry compiler...")
        env = dict(os.environ)
        cmd = [sys.executable, str(COMPILER_SCRIPT)]
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
             return {
                 "status": "warning", 
                 "message": "Skill created but compiler failed.", 
                 "compiler_stderr": result.stderr
             }
             
    except Exception as e:
        return {"status": "warning", "message": f"Compiler execution failed: {str(e)}"}

    return {
        "status": "success",
        "skill_name": skill_name,
        "files_created": [str(md_path), str(meta_path), str(wrapper_path)],
        "compiler_output": result.stdout
    }

