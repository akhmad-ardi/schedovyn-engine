from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

class SnapshotError(ValueError):
    """Raised when the snapshot cannot be represented by this prototype."""


@dataclass(frozen=True)
class PlacementOption:
    """One complete placement candidate for an occurrence."""

    start_slot: int
    end_slot: int
    resources_by_role: dict[str, tuple[str, ...]]
    resource_units: dict[str, int]

    def output_resources(self) -> dict[str, str | list[str]]:
        result: dict[str, str | list[str]] = {}
        for role, resource_ids in self.resources_by_role.items():
            result[role] = (
                resource_ids[0]
                if len(resource_ids) == 1
                else list(resource_ids)
            )
        return result


def parse_time(value: str) -> int:
    """Return minutes after midnight for an HH:MM value."""

    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise SnapshotError(f"Invalid time: {value!r}; expected HH:MM") from exc
    return parsed.hour * 60 + parsed.minute


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SnapshotError(f"Invalid ISO date: {value!r}") from exc


def windows_to_minutes(windows: Iterable[Iterable[str]]) -> list[tuple[int, int]]:
    parsed: list[tuple[int, int]] = []
    for raw_window in windows:
        values = list(raw_window)
        if len(values) != 2:
            raise SnapshotError(f"A time window must have two values: {values!r}")
        start, end = parse_time(values[0]), parse_time(values[1])
        if start >= end:
            raise SnapshotError(f"Time window must have start < end: {values!r}")
        parsed.append((start, end))
    return parsed


def contains_interval(
    start_minute: int,
    end_minute: int,
    windows: Iterable[tuple[int, int]],
) -> bool:
    """Whether [start, end) is fully contained in one allowed window."""

    return any(
        window_start <= start_minute and end_minute <= window_end
        for window_start, window_end in windows
    )


def day_offset(period_start: date, current_date: date) -> int:
    return (current_date - period_start).days


def absolute_slot(
    period_start: date,
    current_date: date,
    minute_of_day: int,
    slot_minutes: int,
) -> int:
    if minute_of_day % slot_minutes != 0:
        raise SnapshotError(
            f"Time {minute_of_day // 60:02d}:{minute_of_day % 60:02d} "
            f"is not aligned to a {slot_minutes}-minute slot"
        )
    # 24 hours are represented even though the organization may be closed for
    # part of the day. This keeps dates independent and makes interval overlap
    # calculations straightforward.
    slots_per_day = (24 * 60) // slot_minutes
    return day_offset(period_start, current_date) * slots_per_day + (
        minute_of_day // slot_minutes
    )


def local_date_time(
    period_start: date,
    slot: int,
    slot_minutes: int,
) -> tuple[date, int]:
    slots_per_day = (24 * 60) // slot_minutes
    offset, slot_in_day = divmod(slot, slots_per_day)
    return period_start + timedelta(days=offset), slot_in_day * slot_minutes

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the scheduling snapshot JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("solver-result.json"),
        help="Path for the JSON solver result",
    )
    return parser.parse_args()
