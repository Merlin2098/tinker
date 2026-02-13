import os
import yaml
import sys
from pathlib import Path

# Paths to Configuration Files
CONFIG_PATH = Path('agent_framework_config.yaml')
RULES_PATH = Path('agent/rules/agent_rules.md')

def validate_config_files():
    """
    Validates that files referenced in configuration exist on disk.
    """
    print("Starting Self-Healing Configuration Validation...")
    errors = []

    # 1. Validate agent_framework_config.yaml
    if not CONFIG_PATH.exists():
        errors.append(f"CRITICAL: Configuration file not found: {CONFIG_PATH}")
    else:
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check framework footprint
            if 'deployment' in config and 'framework_footprint' in config['deployment']:
                for item in config['deployment']['framework_footprint']:
                    if not Path(item).exists():
                        errors.append(f"Missing Framework Footprint Item: {item}")

            # Check static context output path
            if 'static_context' in config and 'output_path' in config['static_context']:
                # output path is a file, check directory exists
                out_path = Path(config['static_context']['output_path'])
                if not out_path.parent.exists():
                     errors.append(f"Missing Directory for Static Context Output: {out_path.parent}")

        except Exception as e:
            errors.append(f"Error parsing {CONFIG_PATH}: {str(e)}")

    # 2. Validate agent_rules.md Protected Files
    if not RULES_PATH.exists():
         errors.append(f"CRITICAL: Governance Rules not found: {RULES_PATH}")
    else:
        # Simple text parsing for protected files block as it is inside markdown
        try:
            with open(RULES_PATH, 'r') as f:
                content = f.read()
            
            # Extract yaml block for protected_files
            import re
            match = re.search(r'protected_files:\n(.*?)(?=\n```)', content, re.DOTALL)
            if match:
                yaml_content = "protected_files:\n" + match.group(1)
                protected_config = yaml.safe_load(yaml_content)
                
                if 'protected_files' in protected_config:
                    for category in protected_config['protected_files']:
                         for file_pattern in protected_config['protected_files'][category]:
                             # Skip glob patterns for now, check explicit files
                             if '*' not in file_pattern:
                                 # Optional project files that might not exist yet
                                 optional_files = ['.env', 'credentials.json', 'pyproject.toml', 'setup.py']
                                 if file_pattern in optional_files:
                                     if not Path(file_pattern).exists():
                                         # Just warn or ignore, don't error
                                         pass 
                                 elif not Path(file_pattern).exists():
                                      errors.append(f"Missing Protected File referenced in Rules: {file_pattern}")
            else:
                errors.append("Could not find protected_files YAML block in agent_rules.md")
                
        except Exception as e:
            errors.append(f"Error parsing protected files in {RULES_PATH}: {str(e)}")

    # Report results
    if errors:
        print("\n[FAIL] VALIDATION FAILED with the following errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n[OK] VALIDATION PASSED. All referenced configuration files exist.")
        sys.exit(0)

if __name__ == "__main__":
    validate_config_files()
