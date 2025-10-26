#!/usr/bin/env python3
"""
ABOUTME: Estimate active development time using git commits and GitHub issue activity
ABOUTME: Run with: python3 scripts/estimate_hours.py
"""

import subprocess
import json
import sys
from datetime import datetime
from typing import List, Tuple


def get_git_commits() -> List[datetime]:
    """Fetch all git commit timestamps"""
    try:
        result = subprocess.run(
            ['git', 'log', '--all', '--pretty=format:%ai'],
            capture_output=True,
            text=True,
            check=True
        )
        commits = [
            datetime.fromisoformat(line.rsplit(' ', 1)[0]).replace(tzinfo=None)
            for line in result.stdout.strip().split('\n')
            if line
        ]
        commits.reverse()  # Oldest first
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error fetching git commits: {e}", file=sys.stderr)
        return []


def get_github_issues() -> List[dict]:
    """Fetch all GitHub issue activity"""
    try:
        result = subprocess.run(
            ['gh', 'issue', 'list', '--state', 'all', '--limit', '100',
             '--json', 'number,createdAt,closedAt,updatedAt'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        print("Warning: Could not fetch GitHub issues (gh CLI not available or not authenticated)", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing GitHub data: {e}", file=sys.stderr)
        return []


def collect_all_activities(commits: List[datetime], issues: List[dict]) -> List[Tuple[str, datetime]]:
    """Combine git commits and GitHub issue events into single timeline"""
    activities = []

    for commit in commits:
        activities.append(('commit', commit))

    for issue in issues:
        created = datetime.fromisoformat(issue['createdAt'].replace('Z', '+00:00')).replace(tzinfo=None)
        activities.append(('issue_created', created))

        if issue['closedAt']:
            closed = datetime.fromisoformat(issue['closedAt'].replace('Z', '+00:00')).replace(tzinfo=None)
            activities.append(('issue_closed', closed))

    activities.sort(key=lambda x: x[1])
    return activities


def estimate_hours(activities: List[Tuple[str, datetime]], threshold_minutes: int) -> float:
    """
    Estimate active hours using commit clustering.

    Assumes gaps > threshold_minutes indicate breaks between work sessions.
    Adds 30 minutes for the final session (average session end time).
    """
    if not activities:
        return 0.0

    timestamps = [a[1] for a in activities]
    total_minutes = 0

    for i in range(1, len(timestamps)):
        diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
        if 0 < diff < threshold_minutes:
            total_minutes += diff

    total_minutes += 30  # Add 30 min for last session
    return total_minutes / 60


def get_daily_breakdown(activities: List[Tuple[str, datetime]]) -> dict:
    """Group activities by date"""
    daily = {}
    for activity_type, timestamp in activities:
        date = timestamp.date()
        if date not in daily:
            daily[date] = {'commits': 0, 'issues': 0}

        if activity_type == 'commit':
            daily[date]['commits'] += 1
        else:
            daily[date]['issues'] += 1

    return daily


def main():
    print("=" * 70)
    print("PORTFOLIO MANAGEMENT PROJECT - TIME ANALYSIS")
    print("=" * 70)

    # Fetch data
    commits = get_git_commits()
    issues = get_github_issues()
    activities = collect_all_activities(commits, issues)

    if not activities:
        print("\nNo activity data found. Make sure you're in a git repository.")
        sys.exit(1)

    # Summary statistics
    print(f"\nData sources:")
    print(f"  Git commits:     {len(commits)}")
    print(f"  GitHub issues:   {len(issues)} ({sum(1 for i in issues if i.get('closedAt'))} closed)")
    print(f"  Total activities: {len(activities)}")

    print(f"\nProject timespan: {activities[0][1].date()} to {activities[-1][1].date()}")
    print(f"Active days: {len(set(a[1].date() for a in activities))}")

    # Daily breakdown
    daily_breakdown = get_daily_breakdown(activities)
    print(f"\nDaily activity breakdown:")
    for date in sorted(daily_breakdown.keys()):
        commits_count = daily_breakdown[date]['commits']
        issues_count = daily_breakdown[date]['issues']
        print(f"  {date}: {commits_count:2d} commits, {issues_count:2d} issue events")

    # Time estimates
    git_only = estimate_hours([(a, t) for a, t in activities if a == 'commit'], 120)
    combined_120 = estimate_hours(activities, 120)
    combined_180 = estimate_hours(activities, 180)

    print(f"\nEstimated active development hours:")
    print(f"  Git commits only (120 min threshold):  {git_only:.1f} hours")
    print(f"  Git + GitHub (120 min threshold):      {combined_120:.1f} hours")
    print(f"  Git + GitHub (180 min threshold):      {combined_180:.1f} hours")

    print("\n" + "=" * 70)
    print(f"RECOMMENDATION: ~{combined_120:.0f}-{combined_180:.0f} hours total active time")
    print("=" * 70)
    print("\nNote: Estimates assume gaps >120/180 min indicate breaks between sessions.")
    print("      GitHub issues capture planning/triage time beyond just coding.")


if __name__ == '__main__':
    main()
