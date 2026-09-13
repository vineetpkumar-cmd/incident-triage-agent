# Notification Quality Judge Calibration

| Case | Factuality | Clarity | Tone | Completeness | Human average | Ollama |
|---|---:|---:|---:|---:|---:|---:|
| HP-001 | 1 | 1 | 1 | 0 | 0.75 | 1.00 |
| HP-011 | 0 | 1 | 1 | 0 | 0.50 | 1.00 |
| EDGE-001 | 1 | 1 | 1 | 0 | 0.75 | 1.00 |
| EDGE-010 | 1 | 1 | 0 | 1 | 0.75 | 1.00 |
| FAIL-005 | 1 | 1 | 0 | 1 | 0.75 | 1.00 |
| ADV-001 | 1 | 1 | 0 | 0 | 0.50 | 1.00 |

Human average = (factuality + clarity + tone + completeness) / 4

The calibration sample shows that the Ollama judge is systematically more
generous than these binary human ratings. Notification-quality results should
therefore be reported as model-judge scores, not as human-validated quality.
