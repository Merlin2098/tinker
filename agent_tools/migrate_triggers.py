
import yaml
from pathlib import Path

REPO_ROOT = Path("c:/Users/User/Documents/Antigravity/tinker")
SKILLS_DIR = REPO_ROOT / "agent/skills"
TRIGGER_ENGINE = SKILLS_DIR / "_trigger_engine.yaml"

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

def migrate_triggers():
    print(f"Reading triggers from {TRIGGER_ENGINE}...")
    engine_data = load_yaml(TRIGGER_ENGINE)
    
    # Map: skill_name -> { match_extensions: [], match_phases: [], ... }
    skill_triggers = {}

    def add_trigger(skill, type, value):
        if skill not in skill_triggers:
            skill_triggers[skill] = {}
        if type not in skill_triggers[skill]:
            skill_triggers[skill][type] = []
        if value not in skill_triggers[skill][type]:
            skill_triggers[skill][type].append(value)

    # 1. Extensions
    for ext, rules in engine_data.get('extension_rules', {}).items():
        for s in rules.get('activate_skills', []) or []:
            add_trigger(s, 'match_extensions', ext)
        for s in rules.get('suggest_skills', []) or []:
            add_trigger(s, 'match_extensions', ext)

    # 2. Phases
    for phase, rules in engine_data.get('phase_rules', {}).items():
        for s in rules.get('activate_skills', []) or []:
            add_trigger(s, 'match_phases', phase)
        for s in rules.get('suggest_skills', []) or []:
            add_trigger(s, 'match_phases', phase)

    # 3. Errors
    for error, rules in engine_data.get('error_rules', {}).items():
        for s in rules.get('activate_skills', []) or []:
            add_trigger(s, 'match_errors', error)
        for s in rules.get('suggest_skills', []) or []:
            add_trigger(s, 'match_errors', error)

    print(f"Found triggers for {len(skill_triggers)} skills.")

    # 4. Inject into .meta.yaml
    meta_files = list(SKILLS_DIR.glob("**/*.meta.yaml"))
    updated_count = 0
    
    for mf in meta_files:
        data = load_yaml(mf)
        name = data.get('name')
        
        if name in skill_triggers:
            print(f"Migrating triggers for {name}...")
            if 'triggers' not in data:
                data['triggers'] = {}
            
            # Merge existing (keywords) with new extracted ones
            t = skill_triggers[name]
            data['triggers'].update(t)
            
            save_yaml(mf, data)
            updated_count += 1
            
    print(f"Migration complete. Updated {updated_count} meta files.")

if __name__ == "__main__":
    migrate_triggers()
