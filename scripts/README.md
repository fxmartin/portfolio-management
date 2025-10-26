# Project Scripts

## estimate_hours.py

Estimate active development time by analyzing git commits and GitHub issue activity.

### Usage

```bash
python3 scripts/estimate_hours.py
```

### What it does

- Analyzes all git commits with timestamps
- Fetches GitHub issue creation/closure events via `gh` CLI
- Clusters activity with configurable time thresholds (assumes gaps >2-3 hours = breaks)
- Shows daily activity breakdown
- Provides multiple estimates (conservative to generous)

### Requirements

- Python 3.7+
- Git repository
- GitHub CLI (`gh`) installed and authenticated (optional, but recommended for accuracy)

### Example Output

```
PORTFOLIO MANAGEMENT PROJECT - TIME ANALYSIS
======================================================================

Data sources:
  Git commits:     27
  GitHub issues:   13 (10 closed)
  Total activities: 50

Project timespan: 2025-10-21 to 2025-10-26
Active days: 4

Daily activity breakdown:
  2025-10-21: 17 commits,  2 issue events
  2025-10-22:  1 commits,  1 issue events
  2025-10-24:  7 commits, 20 issue events
  2025-10-26:  2 commits,  0 issue events

Estimated active development hours:
  Git commits only (120 min threshold):  10.8 hours
  Git + GitHub (120 min threshold):      14.3 hours
  Git + GitHub (180 min threshold):      19.2 hours

======================================================================
RECOMMENDATION: ~14-19 hours total active time
======================================================================
```

### Why GitHub issues improve accuracy

Git commits only capture when code was written. GitHub issues capture:
- Planning and design time (issue creation)
- Bug triage and documentation
- Work sessions that don't immediately result in commits

This typically adds 20-40% to the estimate, making it more realistic.
