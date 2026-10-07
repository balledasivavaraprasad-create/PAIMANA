# Product Principles

## 1. Intelligence over decoration
Every major visual should answer a real question.

## 2. Show change, not only state
Current risk without trend or baseline is incomplete monitoring information.

## 3. Compare before concluding
When sufficient peer evidence exists, contextualize project behavior against relevant peers.

## 4. Never manufacture certainty
The UI must surface uncertainty, conflicting evidence and insufficient peer cohorts.

## 5. Backend is authoritative
Thresholds, events, predictions, investigation state and approval state originate in the backend/domain layer.

## 6. n8n is automation, not business logic
n8n should execute workflows after receiving already-decided events/actions.

## 7. Human approval for consequential actions
Automated alerting is fine. Consequential intervention execution stays behind an explicit authorization boundary.

## 8. Make the agent inspectable
A user should be able to understand what the investigator looked at, what it concluded, what it could not establish, and why it stopped.

## 9. High-class motion, low cognitive noise
Animations should reveal hierarchy, transitions and causal relationships. Avoid floating blobs, gratuitous parallax, looping motion behind dense charts, or motion that interferes with data reading.

## 10. Light mode is a first-class theme
Do not build dark mode and patch light mode later. Every state must be theme-safe.

## 11. Progressive disclosure
Senior users see the signal first. Deep evidence, traces and technical details appear on demand.

## 12. Data lineage matters
Where feasible, show source and timestamp metadata for important facts.

## 13. Graceful degradation
A failed peer service must not blank the entire project page. A failed chart must not crash the dashboard.

## 14. Build from real contracts
Frontend agents should build against documented API schemas and fixture contracts, then replace fixtures with live data.

## 15. Avoid “AI slop” language
Prefer clear domain language such as “Risk Accelerating”, “Peer Deviation”, “Evidence Gap”, “Investigation Ready”, “Observed Outcome”.
