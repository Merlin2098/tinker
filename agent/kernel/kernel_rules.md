# Kernel Rules (Invoker)

The kernel is the always-loaded, minimal governance and bootstrap layer.
It is the single source of truth for:
- authority order (governance > contract > runtime constraints)
- manifest schema location
- minimum skill loader rules
- stop conditions

Kernel rules are static and shared across all agents.
