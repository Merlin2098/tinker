---
description: Update the agent context implementation
---

# Update Context Workflow

This workflow regenerates the static context for the agent framework.

1.  **Validate Configuration Integrity**
    Ensure all referenced files exist before trying to load context.
    ```bash
    python agent_tools/config_validator.py
    ```

// turbo
2.  **Load Static Context**
    Regenerate the context.json file.
    ```bash
    python agent_tools/load_static_context.py
    ```

