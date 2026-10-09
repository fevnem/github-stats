"""Turning a list of days into the numbers the cards draw."""

from __future__ import annotations


def analyse(days: list[dict]) -> tuple[int, int, int, list[tuple[str, int]]]:
    """Return (total, current streak, longest streak, [(week start, week total)]).

    A zero on the final day is treated as "today is not over yet" rather than the
    end of a streak, which is what a reader expects to see mid-morning.
    """
    total = sum(day["contributionCount"] for day in days)

    longest = run = 0
    for day in days:
        run = run + 1 if day["contributionCount"] > 0 else 0
        longest = max(longest, run)

    sequence = list(days)
    if sequence and sequence[-1]["contributionCount"] == 0:
        sequence.pop()
    current = 0
    for day in reversed(sequence):
        if day["contributionCount"] > 0:
            current += 1
        else:
            break

    weeks = [
        (days[i]["date"], sum(day["contributionCount"] for day in days[i:i + 7]))
        for i in range(0, len(days), 7)
    ]
    return total, current, longest, weeks


def as_calendar(days: list[dict], total: int) -> dict:
    """Reshape into GitHub's own week grouping so the field renders identically."""
    buckets: dict[int, list[dict]] = {}
    for day in days:
        buckets.setdefault(day["week"], []).append(day)
    weeks = [
        {"contributionDays": sorted(buckets[key], key=lambda day: day["dow"])}
        for key in sorted(buckets)
    ]
    return {"totalContributions": total, "weeks": weeks}
