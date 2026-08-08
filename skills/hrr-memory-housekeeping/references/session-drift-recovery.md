# Correcting Session Hallucinations & Factual Drift

When a session is found to contain incorrect summaries or stale technical constraints (e.g., Azure vs AWS, hard vs soft deadlines), follow this recovery procedure.

## 1. Deep Root Cause Analysis
- Use `session_search` to find the exact message where the drift began.
- Identify the **Pattern-Match Error**: Did the agent use a stale constraint from the kickoff turn instead of a recent update?
- Check for **Identity Confusion**: Did the agent misidentify a human for an AI agent or vice versa?

## 2. In-Channel Correction
- Do not merely fix it in the current session. **Post a correction thread** in the relevant Slack/Telegram channel.
- **Format**:
    - "Adding a few corrections to the summary above based on latest updates:"
    - List the specific facts being corrected (Hosting, Timeline, Identity).
    - Re-affirm what is "spot on."

## 3. Grounding the Current Session
- Add the corrected fact to the **BA Handoff** document immediately.
- Update **Holographic Memory** with the high-trust corrected fact.
- Re-verify all stakeholder claims in the architecture thread using the **Structured Reasoning** protocol.
