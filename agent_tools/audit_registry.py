
import yaml
from pathlib import Path
import sys

def load_yaml(path):
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def audit_skills(repo_root):
    skills_dir = repo_root / "agent/skills"
    index_path = skills_dir / "_index.yaml"
    
    print(f"Auditing skills in {skills_dir}...")
    
    # 1. Load Index
    index_data = load_yaml(index_path)
    index_list = index_data.get('index', [])
    index_map = {s['name']: s for s in index_list}
    print(f"Found {len(index_list)} skills in _index.yaml")

    # 2. Scan for .meta.yaml files
    meta_files = list(skills_dir.glob("**/*.meta.yaml"))
    print(f"Found {len(meta_files)} .meta.yaml files in filesystem")

    meta_map = {}
    for mf in meta_files:
        data = load_yaml(mf)
        if 'name' in data:
            meta_map[data['name']] = {
                'path': mf,
                'data': data
            }
        else:
            print(f"WARNING: File {mf} has no 'name' field")

    # 3. Compare
    common = set(index_map.keys()) & set(meta_map.keys())
    only_index = set(index_map.keys()) - set(meta_map.keys())
    only_meta = set(meta_map.keys()) - set(index_map.keys())

    print("\n--- AUDIT RESULTS ---")
    
    if only_index:
        print(f"\n[!] MISSING METADATA ({len(only_index)} skills in index but no .meta.yaml):")
        for s in sorted(only_index):
            print(f"  - {s}")
            
    if only_meta:
        print(f"\n[!] UNREGISTERED SKILLS ({len(only_meta)} .meta.yaml files not in index):")
        for s in sorted(only_meta):
            print(f"  - {s} ({meta_map[s]['path']})")

    print(f"\n[OK] {len(common)} skills properly synchronized.")

    # 4. Check for Divergence in Common Skills
    print("\n--- DIVERGENCE CHECK (Index vs Meta) ---")
    divergence_count = 0
    for name in common:
        idx = index_map[name]
        meta = meta_map[name]['data']
        
        # Check tier, cluster, priority
        diffs = []
        for field in ['tier', 'cluster', 'priority']:
            v_idx = idx.get(field)
            v_meta = meta.get(field)
            # Normalize for comparison if needed
            if str(v_idx) != str(v_meta):
                diffs.append(f"{field}: index={v_idx} vs meta={v_meta}")
        
        if diffs:
            print(f"Mismatch in {name}: {', '.join(diffs)}")
            divergence_count += 1
            
    if divergence_count == 0:
        print("No divergences found in common fields.")

if __name__ == "__main__":
    audit_skills(Path("c:/Users/User/Documents/Antigravity/tinker"))
