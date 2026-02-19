# Kernel Rules (Tinker)

The kernel is profile-selection metadata only.

Kernel responsibilities:
- define which profiles are valid (`LITE`, `STANDARD`, `FULL`)
- define default profile
- enforce allowlist-only profile semantics

Kernel non-responsibilities:
- no role routing
- no workflow orchestration
- no trigger-engine policy
- no governance duplication

Capability authorization must come from profile allowlists under `agents/logic/profiles/`.

