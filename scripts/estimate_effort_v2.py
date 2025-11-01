#!/usr/bin/env python3
"""
ABOUTME: Estimate active development time using git commits and GitHub issue activity
ABOUTME: Run with: python3 scripts/estimate_hours.py [options]
ABOUTME: Optimized version with CLI args, structured output, and business metrics
"""

import subprocess
import json
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import os

# Constants
DEFAULT_THRESHOLD_MINUTES = 120
DEFAULT_FINAL_SESSION_MINUTES = 30
CACHE_FILE = ".dev_time_cache.json"


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Estimate development hours from git commits and GitHub issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 estimate_hours.py                     # Default analysis
  python3 estimate_hours.py --format json       # JSON output for automation
  python3 estimate_hours.py --threshold 180     # 3-hour session threshold
  python3 estimate_hours.py --since 2024-10-01  # Analysis since October 1st
  python3 estimate_hours.py --cache --verbose   # Use cache with debug output
        """,
    )

    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD_MINUTES,
        help=f"Session gap threshold in minutes (default: {DEFAULT_THRESHOLD_MINUTES})",
    )
    parser.add_argument(
        "--final-session",
        type=int,
        default=DEFAULT_FINAL_SESSION_MINUTES,
        help=f"Minutes to add for final session (default: {DEFAULT_FINAL_SESSION_MINUTES})",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--since", type=str, help="Start date for analysis (YYYY-MM-DD)"
    )
    parser.add_argument("--until", type=str, help="End date for analysis (YYYY-MM-DD)")
    parser.add_argument(
        "--cache", action="store_true", help="Use cached data if available"
    )
    parser.add_argument(
        "--no-github", action="store_true", help="Skip GitHub data fetching"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser.parse_args()


def load_cache() -> Optional[Dict]:
    """Load cached data if available and recent"""
    try:
        if Path(CACHE_FILE).exists():
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)

            # Check if cache is less than 1 hour old
            cache_time = datetime.fromisoformat(cache.get("timestamp", ""))
            if datetime.now() - cache_time < timedelta(hours=1):
                logging.info("Using cached data (less than 1 hour old)")
                return cache
            else:
                logging.info("Cache expired, fetching fresh data")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logging.warning(f"Cache file corrupted: {e}")

    return None


def save_cache(data: Dict):
    """Save data to cache"""
    try:
        cache_data = {"timestamp": datetime.now().isoformat(), "data": data}
        with open(CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
        logging.debug("Data cached successfully")
    except Exception as e:
        logging.warning(f"Failed to save cache: {e}")


def get_git_commits(
    since: Optional[datetime] = None, until: Optional[datetime] = None
) -> List[datetime]:
    """Fetch git commit timestamps with optional date filtering"""
    try:
        cmd = ["git", "log", "--all", "--pretty=format:%ai"]

        if since:
            cmd.extend(["--since", since.isoformat()])
        if until:
            cmd.extend(["--until", until.isoformat()])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    # Parse git timestamp format
                    commit_time = datetime.fromisoformat(
                        line.rsplit(" ", 1)[0]
                    ).replace(tzinfo=None)
                    commits.append(commit_time)
                except ValueError as e:
                    logging.warning(f"Failed to parse commit timestamp: {line} - {e}")

        commits.reverse()  # Oldest first
        logging.info(f"Fetched {len(commits)} git commits")
        return commits

    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching git commits: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error fetching commits: {e}")
        return []


def get_github_issues() -> List[dict]:
    """Fetch GitHub issue activity with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--state",
                    "all",
                    "--limit",
                    "100",
                    "--json",
                    "number,createdAt,closedAt,updatedAt,title,state",
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,  # 30 second timeout
            )

            issues = json.loads(result.stdout)
            logging.info(f"Fetched {len(issues)} GitHub issues")
            return issues

        except subprocess.CalledProcessError as e:
            if attempt == 0:
                logging.warning(
                    "GitHub CLI not available or not authenticated - continuing without GitHub data"
                )
            return []
        except subprocess.TimeoutExpired:
            logging.warning(f"GitHub API timeout (attempt {attempt + 1}/{max_retries})")
            if attempt == max_retries - 1:
                logging.error(
                    "GitHub API consistently timing out - skipping GitHub data"
                )
                return []
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing GitHub data: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error fetching GitHub issues: {e}")
            return []

    return []


def filter_activities_by_date(
    activities: List[Tuple[str, datetime]],
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> List[Tuple[str, datetime]]:
    """Filter activities by date range"""
    filtered = activities

    if since:
        filtered = [(a, t) for a, t in filtered if t >= since]
    if until:
        filtered = [(a, t) for a, t in filtered if t <= until]

    logging.info(f"Filtered to {len(filtered)} activities in date range")
    return filtered


def collect_all_activities(
    commits: List[datetime], issues: List[dict]
) -> List[Tuple[str, datetime]]:
    """Combine git commits and GitHub issue events into single timeline"""
    activities = []

    # Add commits
    for commit in commits:
        activities.append(("commit", commit))

    # Add issue events
    for issue in issues:
        try:
            created = datetime.fromisoformat(
                issue["createdAt"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            activities.append(("issue_created", created))

            if issue.get("closedAt"):
                closed = datetime.fromisoformat(
                    issue["closedAt"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                activities.append(("issue_closed", closed))
        except (ValueError, KeyError) as e:
            logging.warning(f"Failed to parse issue timestamp: {e}")

    activities.sort(key=lambda x: x[1])
    logging.info(f"Combined {len(activities)} total activities")
    return activities


def estimate_hours(
    activities: List[Tuple[str, datetime]],
    threshold_minutes: int,
    final_session_minutes: int,
) -> float:
    """
    Estimate active hours using commit clustering.

    Assumes gaps > threshold_minutes indicate breaks between work sessions.
    Adds final_session_minutes for the last session.
    """
    if not activities:
        return 0.0

    timestamps = [a[1] for a in activities]
    total_minutes = 0
    session_count = 0

    for i in range(1, len(timestamps)):
        diff = (timestamps[i] - timestamps[i - 1]).total_seconds() / 60
        if 0 < diff < threshold_minutes:
            total_minutes += diff
        else:
            session_count += 1

    total_minutes += final_session_minutes  # Add time for final session
    logging.debug(
        f"Estimated {session_count + 1} work sessions, {total_minutes:.1f} total minutes"
    )

    return total_minutes / 60


def calculate_velocity_metrics(
    commits: List[datetime], issues: List[dict], activities: List[Tuple[str, datetime]]
) -> Dict:
    """Calculate development velocity and efficiency metrics"""
    if not activities:
        return {}

    # Basic counts
    closed_issues = [i for i in issues if i.get("closedAt")]
    active_days = len(set(a[1].date() for a in activities))

    # Calculate metrics
    metrics = {
        "total_commits": len(commits),
        "total_issues": len(issues),
        "closed_issues": len(closed_issues),
        "active_days": active_days,
        "story_completion_rate": len(closed_issues) / len(issues) if issues else 0,
        "avg_commits_per_day": len(commits) / active_days if active_days > 0 else 0,
        "avg_activities_per_day": len(activities) / active_days
        if active_days > 0
        else 0,
        "project_span_days": (activities[-1][1].date() - activities[0][1].date()).days
        + 1
        if activities
        else 0,
    }

    # Calculate development intensity (activities per active day)
    metrics["development_intensity"] = metrics["avg_activities_per_day"]

    logging.debug(f"Calculated velocity metrics: {metrics}")
    return metrics


def get_daily_breakdown(activities: List[Tuple[str, datetime]]) -> Dict:
    """Group activities by date"""
    daily = {}
    for activity_type, timestamp in activities:
        date = timestamp.date()
        if date not in daily:
            daily[date] = {"commits": 0, "issues": 0}

        if activity_type == "commit":
            daily[date]["commits"] += 1
        else:
            daily[date]["issues"] += 1

    return daily


def output_text_format(data: Dict, args) -> str:
    """Generate human-readable text output"""
    activities = data["activities"]
    metrics = data["metrics"]
    estimates = data["estimates"]

    output = []
    output.append("=" * 70)
    output.append("PORTFOLIO MANAGEMENT PROJECT - TIME ANALYSIS")
    output.append("=" * 70)

    # Data sources
    output.append(f"\nData sources:")
    output.append(f"  Git commits:     {metrics.get('total_commits', 0)}")
    output.append(
        f"  GitHub issues:   {metrics.get('total_issues', 0)} ({metrics.get('closed_issues', 0)} closed)"
    )
    output.append(f"  Total activities: {len(activities)}")

    if activities:
        output.append(
            f"\nProject timespan: {activities[0][1].date()} to {activities[-1][1].date()}"
        )
        output.append(f"Active days: {metrics.get('active_days', 0)}")

        # Velocity metrics
        output.append(f"\nVelocity metrics:")
        output.append(
            f"  Commits per day:     {metrics.get('avg_commits_per_day', 0):.1f}"
        )
        output.append(
            f"  Activities per day:  {metrics.get('avg_activities_per_day', 0):.1f}"
        )
        output.append(
            f"  Issue completion:    {metrics.get('story_completion_rate', 0):.1%}"
        )
        output.append(
            f"  Development intensity: {metrics.get('development_intensity', 0):.1f}"
        )

        # Time estimates
        output.append(f"\nEstimated active development hours:")
        for estimate in estimates:
            threshold = estimate["threshold_minutes"]
            hours = estimate["hours"]
            output.append(f"  {threshold} min threshold: {hours:.1f} hours")

    output.append("\n" + "=" * 70)
    recommended = estimates[0]["hours"] if estimates else 0
    output.append(f"RECOMMENDATION: ~{recommended:.0f} hours total active time")
    output.append("=" * 70)

    return "\n".join(output)


def output_json_format(data: Dict, args) -> str:
    """Generate machine-readable JSON output"""
    # Make data JSON serializable
    serializable_data = {
        "metadata": {
            "analysis_date": datetime.now().isoformat(),
            "threshold_minutes": args.threshold,
            "final_session_minutes": args.final_session,
            "date_range": {"since": args.since, "until": args.until},
        },
        "metrics": data["metrics"],
        "estimates": data["estimates"],
        "summary": {
            "recommended_hours": data["estimates"][0]["hours"]
            if data["estimates"]
            else 0,
            "total_activities": len(data["activities"]),
            "analysis_period_days": data["metrics"].get("project_span_days", 0),
        },
    }

    return json.dumps(serializable_data, indent=2)


def main():
    """Main execution function"""
    args = parse_args()
    setup_logging(args.verbose)

    logging.info("Starting development time analysis")

    # Parse date filters
    since_date = None
    until_date = None

    if args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            logging.error(f"Invalid since date format: {args.since}. Use YYYY-MM-DD")
            sys.exit(1)

    if args.until:
        try:
            until_date = datetime.strptime(args.until, "%Y-%m-%d")
        except ValueError:
            logging.error(f"Invalid until date format: {args.until}. Use YYYY-MM-DD")
            sys.exit(1)

    # Try to load from cache
    cached_data = None
    if args.cache:
        cached_data = load_cache()

    if cached_data:
        commits = cached_data["data"]["commits"]
        issues = cached_data["data"]["issues"]
        # Convert string timestamps back to datetime objects
        commits = [datetime.fromisoformat(c) for c in commits]
        # Issues are already in the right format
    else:
        # Fetch fresh data
        commits = get_git_commits(since_date, until_date)
        issues = [] if args.no_github else get_github_issues()

        # Save to cache
        if not args.cache:  # Only save if we fetched fresh data
            cache_data = {"commits": [c.isoformat() for c in commits], "issues": issues}
            save_cache(cache_data)

    # Combine activities
    activities = collect_all_activities(commits, issues)

    # Apply date filtering to activities
    activities = filter_activities_by_date(activities, since_date, until_date)

    if not activities:
        logging.error(
            "No activity data found. Make sure you're in a git repository with commits."
        )
        sys.exit(1)

    # Calculate metrics
    metrics = calculate_velocity_metrics(commits, issues, activities)

    # Generate estimates with different thresholds
    estimates = []
    thresholds = [args.threshold]
    if args.threshold != 180:  # Add 180 if not already specified
        thresholds.append(180)
    if args.threshold != 120:  # Add 120 if not already specified
        thresholds.append(120)

    for threshold in sorted(set(thresholds)):
        hours = estimate_hours(activities, threshold, args.final_session)
        estimates.append({"threshold_minutes": threshold, "hours": hours})

    # Prepare output data
    output_data = {"activities": activities, "metrics": metrics, "estimates": estimates}

    # Generate output
    if args.format == "json":
        print(output_json_format(output_data, args))
    else:
        print(output_text_format(output_data, args))

    logging.info("Analysis completed successfully")


if __name__ == "__main__":
    main()
