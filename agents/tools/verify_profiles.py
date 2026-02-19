
from agents.tools._profile_state import load_profile_definition
import sys

def verify():
    profiles = ["LITE", "STANDARD", "FULL"]
    
    for p in profiles:
        print(f"--- Resolving {p} ---")
        data = load_profile_definition(p)
        skills = data.get("capabilities", {}).get("allowlist", {}).get("skills", [])
        clusters = data.get("capabilities", {}).get("allowlist", {}).get("clusters", [])
        
        print(f"Inheritance Chain: {data.get('inherits', 'None')} -> ...")
        print(f"Total Skills: {len(skills)}")
        print(f"Total Clusters: {len(clusters)}")
        
        # Spot checks
        if "skill_authority_first" in skills:
            print("[OK] inherited 'skill_authority_first' from _BASE")
        else:
            print("[FAIL] Missing 'skill_authority_first' from _BASE")

        if p == "FULL":
            if "git_rollback_strategy" in skills:
                 print("[OK] found 'git_rollback_strategy' (FULL specific)")
            else:
                 print("[FAIL] Missing 'git_rollback_strategy'")

if __name__ == "__main__":
    verify()

