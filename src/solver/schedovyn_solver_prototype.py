"""Schedovyn pilot-training solver prototype.

This prototype models the snapshot contract with OR-Tools CP-SAT.

Usage:
    python schedovyn_solver.py \
        --input Snapshot-input-contoh.json \
        --output solver-result.json

The input file is expected to contain one scheduling snapshot. The reference
assignment is intentionally not used as a solver constraint: it is an example
of an acceptable result, while CP-SAT is free to find another valid schedule.

Implemented hard rules for the pilot:
    H01  Resource concurrent capacity / no over-capacity overlap
    H02  Resource availability, including date overrides
    H03  Resource compatibility (type, tags, seats, candidates)
    H04  Duration and activity allowed windows
    H05  Organization calendar, open windows, holidays
    H06  Locked occurrence placement
    H07  Maximum daily resource load
    H08  Published bookings, excluding the schedule version being replaced
    H09  Every required occurrence receives exactly one complete placement

Implemented preferences:
    - preferred_time, including full_interval matching
    - preferred_resource

The prototype uses local date/time values from the workspace. This is
appropriate for the pilot snapshot, whose scheduling times are already given
in the workspace timezone (Asia/Makassar). A production worker should use a
timezone-aware datetime layer at the snapshot boundary.
"""

from __future__ import annotations

import argparse
import itertools
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from ortools.sat.python import cp_model


JsonObject = dict[str, Any]


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


class PilotSolver:
    """Build and solve a CP-SAT model for a Schedovyn snapshot."""

    def __init__(self, snapshot: JsonObject) -> None:
        self.snapshot = snapshot
        self.model = cp_model.CpModel()

        period = snapshot.get("period", {})
        self.period_start = parse_date(period["start_date"])
        self.period_end = parse_date(period["end_date"])
        self.slot_minutes = int(period["slot_minutes"])
        if self.slot_minutes <= 0 or (24 * 60) % self.slot_minutes != 0:
            raise SnapshotError(
                "period.slot_minutes must be a positive divisor of 1440"
            )

        self.calendar = snapshot.get("calendar", {})
        self.calendar_open_windows = windows_to_minutes(
            self.calendar.get("open_windows", [])
        )
        self.holidays = {
            parse_date(value) for value in self.calendar.get("holidays", [])
        }

        self.resources: dict[str, JsonObject] = {
            resource["id"]: resource
            for resource in snapshot.get("resources", [])
        }
        self.activities: dict[str, JsonObject] = {
            activity["id"]: activity
            for activity in snapshot.get("activities", [])
        }
        self.occurrences: list[JsonObject] = list(
            snapshot.get("occurrences", [])
        )
        self.availability_profiles: dict[str, JsonObject] = {
            profile["id"]: profile
            for profile in snapshot.get("availability_profiles", [])
        }
        self.availability_overrides: dict[tuple[str, date], JsonObject] = {
            (override["resource_id"], parse_date(override["date"])): override
            for override in snapshot.get("availability_overrides", [])
        }
        self.locks: dict[str, JsonObject] = {
            lock["occurrence_id"]: lock
            for lock in snapshot.get("locks", [])
        }

        # For each occurrence, retain the candidate metadata and its selection
        # Boolean variables. They are used by constraints, objective, and
        # result extraction.
        self.options_by_occurrence: dict[str, list[PlacementOption]] = {}
        self.option_vars_by_occurrence: dict[str, list[cp_model.IntVar]] = {}
        self.preference_pairs: list[dict[str, Any]] = []

    def build(self) -> None:
        self._validate_snapshot_references()
        self._build_occurrence_options()
        self._add_hard_rules()
        self._add_preferences()

    def solve(self) -> JsonObject:
        self.build()

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(
            self.snapshot.get("solver_budget_seconds", 60)
        )
        solver.parameters.num_search_workers = 8

        status = solver.Solve(self.model)
        status_name = solver.StatusName(status)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assignments = self._extract_assignments(solver)
            preference = self._extract_preference_summary(solver)
            solution_status = (
                "Optimal" if status == cp_model.OPTIMAL else "Feasible"
            )
            return {
                "schema_version": "pilot-training-solver-result-1.0.0",
                "dataset_id": self.snapshot.get("dataset_id"),
                "input_revision": self.snapshot.get("input_revision"),
                "solution_status": solution_status,
                "solver_status": status_name,
                "assignments": assignments,
                "unassigned_occurrences": [],
                "preference": preference,
                "solver": {
                    "objective_value": solver.ObjectiveValue(),
                    "best_objective_bound": solver.BestObjectiveBound(),
                    "wall_time_seconds": solver.WallTime(),
                    "num_conflicts": solver.NumConflicts(),
                    "num_branches": solver.NumBranches(),
                },
            }

        if status == cp_model.INFEASIBLE:
            return {
                "schema_version": "pilot-training-solver-result-1.0.0",
                "dataset_id": self.snapshot.get("dataset_id"),
                "input_revision": self.snapshot.get("input_revision"),
                "solution_status": "Infeasible",
                "solver_status": status_name,
                "assignments": [],
                "unassigned_occurrences": [
                    occurrence["id"] for occurrence in self.occurrences
                ],
                "preference": self._empty_preference_summary(),
                "diagnostics": {
                    "message": (
                        "CP-SAT membuktikan bahwa seluruh hard constraint "
                        "tidak dapat dipenuhi secara bersamaan."
                    )
                },
            }

        # UNKNOWN includes a time limit without a complete solution. It must
        # not be reported as infeasible.
        return {
            "schema_version": "pilot-training-solver-result-1.0.0",
            "dataset_id": self.snapshot.get("dataset_id"),
            "input_revision": self.snapshot.get("input_revision"),
            "solution_status": "Belum ditemukan",
            "solver_status": status_name,
            "assignments": [],
            "unassigned_occurrences": [
                occurrence["id"] for occurrence in self.occurrences
            ],
            "preference": self._empty_preference_summary(),
            "diagnostics": {
                "message": (
                    "Batas waktu tercapai tanpa jadwal lengkap dan tanpa "
                    "bukti infeasible."
                )
            },
        }

    def _validate_snapshot_references(self) -> None:
        if self.period_end < self.period_start:
            raise SnapshotError("period.end_date must not precede start_date")

        for occurrence in self.occurrences:
            occurrence_id = occurrence["id"]
            activity_id = occurrence["activity_id"]
            if activity_id not in self.activities:
                raise SnapshotError(
                    f"Occurrence {occurrence_id} references unknown activity "
                    f"{activity_id}"
                )
            occurrence_date = parse_date(occurrence["date"])
            if not self.period_start <= occurrence_date <= self.period_end:
                raise SnapshotError(
                    f"Occurrence {occurrence_id} is outside the planning period"
                )

        replacing_version_id = self.snapshot.get("replaces_schedule_version_id")
        for booking in self.snapshot.get("published_bookings", []):
            if booking.get("workspace_id") != self.snapshot["workspace"]["id"]:
                continue
            if booking.get("schedule_version_id") == replacing_version_id:
                continue
            for resource_id in booking.get("resource_units", {}):
                if resource_id not in self.resources:
                    raise SnapshotError(
                        f"Booking {booking.get('id')} references unknown resource "
                        f"{resource_id}"
                    )

    def _build_occurrence_options(self) -> None:
        for occurrence in self.occurrences:
            occurrence_id = occurrence["id"]
            activity = self.activities[occurrence["activity_id"]]
            occurrence_date = parse_date(occurrence["date"])
            options = self._generate_options_for_occurrence(
                occurrence, activity, occurrence_date
            )
            self.options_by_occurrence[occurrence_id] = options

            variables: list[cp_model.IntVar] = []
            for index, _ in enumerate(options):
                variables.append(
                    self.model.NewBoolVar(f"select_{occurrence_id}_{index}")
                )
            self.option_vars_by_occurrence[occurrence_id] = variables

    def _generate_options_for_occurrence(
        self,
        occurrence: JsonObject,
        activity: JsonObject,
        occurrence_date: date,
    ) -> list[PlacementOption]:
        # H03: generate valid candidate resource combinations first.
        role_candidates: list[tuple[str, list[tuple[str, ...]], JsonObject]] = []
        for requirement in activity.get("requirements", []):
            role = requirement["role"]
            candidates = self._candidate_resource_ids(requirement)
            combinations = list(
                itertools.combinations(
                    candidates, int(requirement.get("select_count", 1))
                )
            )
            if not combinations:
                return []
            role_candidates.append((role, combinations, requirement))

        activity_windows = windows_to_minutes(
            activity.get("allowed_windows", [])
        )
        duration_minutes = int(activity["duration_minutes"])
        if duration_minutes <= 0 or duration_minutes % self.slot_minutes != 0:
            raise SnapshotError(
                f"Activity {activity['id']} duration must be a positive "
                f"multiple of slot_minutes"
            )

        # H05 + H04: possible starts are restricted by both organization and
        # activity windows. Resource availability is checked per combination.
        possible_starts: list[int] = []
        if (
            occurrence_date.weekday() + 1 in self.calendar.get("iso_weekdays", [])
            and occurrence_date not in self.holidays
        ):
            for window_start, window_end in self.calendar_open_windows:
                for start_minute in range(
                    window_start,
                    window_end - duration_minutes + 1,
                    self.slot_minutes,
                ):
                    end_minute = start_minute + duration_minutes
                    if contains_interval(
                        start_minute, end_minute, activity_windows
                    ):
                        possible_starts.append(
                            absolute_slot(
                                self.period_start,
                                occurrence_date,
                                start_minute,
                                self.slot_minutes,
                            )
                        )

        options: list[PlacementOption] = []
        for start_slot in possible_starts:
            end_slot = start_slot + duration_minutes // self.slot_minutes
            start_date, start_minute = local_date_time(
                self.period_start, start_slot, self.slot_minutes
            )
            _, end_minute = local_date_time(
                self.period_start, end_slot, self.slot_minutes
            )
            if start_date != occurrence_date or end_minute <= start_minute:
                # The pilot does not support activities crossing midnight.
                continue

            for combinations in itertools.product(
                *(item[1] for item in role_candidates)
            ):
                selected_resource_ids = [
                    resource_id
                    for resource_group in combinations
                    for resource_id in resource_group
                ]
                # A resource cannot satisfy two distinct requirements at the
                # same time unless the input explicitly models that as one
                # requirement with multiple units.
                if len(selected_resource_ids) != len(set(selected_resource_ids)):
                    continue

                if not all(
                    self._resource_available_for_interval(
                        resource_id,
                        occurrence_date,
                        start_minute,
                        start_minute + duration_minutes,
                    )
                    for resource_id in selected_resource_ids
                ):
                    continue

                resources_by_role: dict[str, tuple[str, ...]] = {}
                resource_units: dict[str, int] = {}
                for (role, _, requirement), selected in zip(
                    role_candidates, combinations
                ):
                    resources_by_role[role] = tuple(selected)
                    units = int(requirement.get("units_per_selected_resource", 1))
                    if units <= 0:
                        raise SnapshotError(
                            f"Requirement {role} must request positive units"
                        )
                    for resource_id in selected:
                        resource_units[resource_id] = units

                option = PlacementOption(
                    start_slot=start_slot,
                    end_slot=end_slot,
                    resources_by_role=resources_by_role,
                    resource_units=resource_units,
                )
                if self._matches_lock(occurrence, option):
                    options.append(option)

        return options

    def _candidate_resource_ids(self, requirement: JsonObject) -> list[str]:
        fixed_resource_id = requirement.get("fixed_resource_id")
        requested_ids = requirement.get("candidate_ids")
        if fixed_resource_id is not None:
            candidate_ids = [fixed_resource_id]
        elif requested_ids:
            candidate_ids = list(requested_ids)
        else:
            candidate_ids = list(self.resources)

        required_tags = set(requirement.get("required_tags", []))
        min_seats = int(requirement.get("min_seats", 0))
        min_participants = int(requirement.get("min_participants", 0))

        result: list[str] = []
        for resource_id in candidate_ids:
            resource = self.resources.get(resource_id)
            if resource is None or not resource.get("active", False):
                continue
            if resource.get("type") != requirement.get("type"):
                continue
            if not required_tags.issubset(set(resource.get("tags", []))):
                continue
            if int(resource.get("seats", 0)) < min_seats:
                continue
            if int(resource.get("participant_count", 0)) < min_participants:
                continue
            result.append(resource_id)
        return result

    def _resource_available_for_interval(
        self,
        resource_id: str,
        current_date: date,
        start_minute: int,
        end_minute: int,
    ) -> bool:
        resource = self.resources[resource_id]
        override = self.availability_overrides.get((resource_id, current_date))
        if override is not None:
            windows = windows_to_minutes(override.get("available_windows", []))
        else:
            profile_id = resource.get("availability_profile_id")
            profile = self.availability_profiles.get(profile_id, {})
            if current_date.isoweekday() not in profile.get("iso_weekdays", []):
                return False
            windows = windows_to_minutes(profile.get("windows", []))
        return contains_interval(start_minute, end_minute, windows)

    def _matches_lock(
        self,
        occurrence: JsonObject,
        option: PlacementOption,
    ) -> bool:
        lock = self.locks.get(occurrence["id"])
        if lock is None:
            return True

        locked_resources = lock.get("resources", {})

        if set(locked_resources) != set(option.resources_by_role):
            return False

        for role, locked_value in locked_resources.items():
            entries = (
                locked_value
                if isinstance(locked_value, list)
                else [locked_value]
            )

            expected_ids = []
            expected_units = {}

            for entry in entries:
                if isinstance(entry, str):
                    resource_id = entry
                elif isinstance(entry, dict):
                    resource_id = entry["resource_id"]
                    expected_units[resource_id] = entry["units"]
                else:
                    raise SnapshotError(
                        f"Invalid lock resource format for role {role}"
                    )

                expected_ids.append(resource_id)

            if len(expected_ids) != len(set(expected_ids)):
                raise SnapshotError(
                    f"Duplicate resource in lock role {role}"
                )

            actual_ids = option.resources_by_role[role]

            # Urutan orang dalam satu role tidak memengaruhi kesamaan lock.
            if set(actual_ids) != set(expected_ids):
                return False

            for resource_id, units in expected_units.items():
                if option.resource_units.get(resource_id) != units:
                    return False

        return True

    def _add_hard_rules(self) -> None:
        # H09: every occurrence is assigned exactly one complete placement.
        for occurrence in self.occurrences:
            occurrence_id = occurrence["id"]
            variables = self.option_vars_by_occurrence[occurrence_id]
            if not variables:
                if occurrence.get("required", True):
                    self.model.AddBoolOr([])
            elif occurrence.get("required", True):
                self.model.AddExactlyOne(variables)
            else:
                self.model.AddAtMostOne(variables)

        # H01 + H08: one cumulative constraint per resource. Optional
        # intervals are selected only when their placement option is selected;
        # published bookings are mandatory intervals in the same capacity pool.
        intervals_by_resource: dict[str, list[cp_model.IntervalVar]] = {
            resource_id: [] for resource_id in self.resources
        }
        demands_by_resource: dict[str, list[int]] = {
            resource_id: [] for resource_id in self.resources
        }

        for occurrence in self.occurrences:
            occurrence_id = occurrence["id"]
            for index, option in enumerate(self.options_by_occurrence[occurrence_id]):
                selected = self.option_vars_by_occurrence[occurrence_id][index]
                size = option.end_slot - option.start_slot
                for resource_id, units in option.resource_units.items():
                    interval = self.model.NewOptionalIntervalVar(
                        option.start_slot,
                        size,
                        option.end_slot,
                        selected,
                        f"interval_{occurrence_id}_{index}_{resource_id}",
                    )
                    intervals_by_resource[resource_id].append(interval)
                    demands_by_resource[resource_id].append(units)

        self._add_published_booking_intervals(
            intervals_by_resource, demands_by_resource
        )

        for resource_id, intervals in intervals_by_resource.items():
            if not intervals:
                continue
            capacity = int(self.resources[resource_id].get("concurrent_capacity", 1))
            if capacity <= 0:
                raise SnapshotError(
                    f"Resource {resource_id} must have positive concurrent_capacity"
                )
            self.model.AddCumulative(
                intervals,
                demands_by_resource[resource_id],
                capacity,
            )

        # H07: daily load is counted in resource-minutes, including units used
        # by one selected option. This is separate from concurrent capacity.
        for resource_id, resource in self.resources.items():
            daily_limit = resource.get("max_daily_minutes")
            if daily_limit is None:
                continue
            daily_limit = int(daily_limit)
            for current_date in self._planning_dates():
                load_terms: list[cp_model.LinearExpr] = []
                for occurrence in self.occurrences:
                    if parse_date(occurrence["date"]) != current_date:
                        continue
                    occurrence_id = occurrence["id"]
                    activity = self.activities[occurrence["activity_id"]]
                    duration = int(activity["duration_minutes"])
                    for index, option in enumerate(
                        self.options_by_occurrence[occurrence_id]
                    ):
                        units = option.resource_units.get(resource_id, 0)
                        if units:
                            load_terms.append(
                                units
                                * duration
                                * self.option_vars_by_occurrence[occurrence_id][
                                    index
                                ]
                            )

                booking_load = self._published_booking_daily_load(
                    resource_id, current_date
                )
                if load_terms or booking_load:
                    self.model.Add(sum(load_terms, booking_load) <= daily_limit)

    def _add_published_booking_intervals(
        self,
        intervals_by_resource: dict[str, list[cp_model.IntervalVar]],
        demands_by_resource: dict[str, list[int]],
    ) -> None:
        replacing_version_id = self.snapshot.get("replaces_schedule_version_id")
        workspace_id = self.snapshot["workspace"]["id"]
        for booking in self.snapshot.get("published_bookings", []):
            if booking.get("workspace_id") != workspace_id:
                continue
            if booking.get("schedule_version_id") == replacing_version_id:
                continue

            booking_date = parse_date(booking["date"])
            start = parse_time(booking["start"])
            end = parse_time(booking["end"])
            if end <= start:
                raise SnapshotError(f"Booking {booking['id']} crosses midnight")
            start_slot = absolute_slot(
                self.period_start, booking_date, start, self.slot_minutes
            )
            end_slot = absolute_slot(
                self.period_start, booking_date, end, self.slot_minutes
            )
            for resource_id, units in booking.get("resource_units", {}).items():
                interval = self.model.NewIntervalVar(
                    start_slot,
                    end_slot - start_slot,
                    end_slot,
                    f"booking_{booking['id']}_{resource_id}",
                )
                intervals_by_resource[resource_id].append(interval)
                demands_by_resource[resource_id].append(int(units))

    def _published_booking_daily_load(
        self,
        resource_id: str,
        current_date: date,
    ) -> int:
        replacing_version_id = self.snapshot.get("replaces_schedule_version_id")
        workspace_id = self.snapshot["workspace"]["id"]
        total = 0
        for booking in self.snapshot.get("published_bookings", []):
            if booking.get("workspace_id") != workspace_id:
                continue
            if booking.get("schedule_version_id") == replacing_version_id:
                continue
            if parse_date(booking["date"]) != current_date:
                continue
            start = parse_time(booking["start"])
            end = parse_time(booking["end"])
            total += (end - start) * int(
                booking.get("resource_units", {}).get(resource_id, 0)
            )
        return total

    def _add_preferences(self) -> None:
        objective_terms: list[cp_model.LinearExpr] = []
        for preference in self.snapshot.get("preferences", []):
            if not preference.get("active", True):
                continue
            weight = int(preference.get("weight", 0))
            if weight <= 0:
                raise SnapshotError(
                    f"Preference {preference.get('id')} must have positive weight"
                )

            relevant_occurrences = [
                occurrence
                for occurrence in self.occurrences
                if occurrence["activity_id"] in preference.get("activity_ids", [])
            ]
            for occurrence in relevant_occurrences:
                occurrence_id = occurrence["id"]
                matching_vars: list[cp_model.IntVar] = []
                for index, option in enumerate(
                    self.options_by_occurrence[occurrence_id]
                ):
                    if self._option_matches_preference(option, preference):
                        matching_vars.append(
                            self.option_vars_by_occurrence[occurrence_id][index]
                        )
                        objective_terms.append(
                            weight
                            * self.option_vars_by_occurrence[occurrence_id][index]
                        )
                self.preference_pairs.append(
                    {
                        "preference_id": preference.get("id"),
                        "occurrence_id": occurrence_id,
                        "weight": weight,
                        "matching_vars": matching_vars,
                    }
                )

        if objective_terms:
            self.model.Maximize(sum(objective_terms))

    def _option_matches_preference(
        self,
        option: PlacementOption,
        preference: JsonObject,
    ) -> bool:
        preference_type = preference.get("type")
        if preference_type == "preferred_time":
            start_date, start_minute = local_date_time(
                self.period_start, option.start_slot, self.slot_minutes
            )
            end_date, end_minute = local_date_time(
                self.period_start, option.end_slot, self.slot_minutes
            )
            if start_date != end_date:
                return False
            window = windows_to_minutes([preference["window"]])
            if preference.get("match", "full_interval") == "full_interval":
                return contains_interval(
                    start_minute, end_minute, window
                )
            if preference.get("match") == "start_in_window":
                return any(
                    window_start <= start_minute < window_end
                    for window_start, window_end in window
                )
            raise SnapshotError(
                f"Unsupported preferred_time match: {preference.get('match')}"
            )

        if preference_type == "preferred_resource":
            role = preference["role"]
            preferred_ids = set(preference.get("resource_ids", []))
            return bool(
                preferred_ids.intersection(
                    option.resources_by_role.get(role, ())
                )
            )

        raise SnapshotError(
            f"Unsupported preference type: {preference_type!r}"
        )

    def _extract_assignments(self, solver: cp_model.CpSolver) -> list[JsonObject]:
        assignments: list[JsonObject] = []
        for occurrence in self.occurrences:
            occurrence_id = occurrence["id"]
            variables = self.option_vars_by_occurrence[occurrence_id]
            selected_index = next(
                (
                    index
                    for index, variable in enumerate(variables)
                    if solver.Value(variable) == 1
                ),
                None,
            )
            if selected_index is None:
                continue

            option = self.options_by_occurrence[occurrence_id][selected_index]
            _, start_minute = local_date_time(
                self.period_start, option.start_slot, self.slot_minutes
            )
            _, end_minute = local_date_time(
                self.period_start, option.end_slot, self.slot_minutes
            )
            assignments.append(
                {
                    "occurrence_id": occurrence_id,
                    "date": occurrence["date"],
                    "start": f"{start_minute // 60:02d}:{start_minute % 60:02d}",
                    "end": f"{end_minute // 60:02d}:{end_minute % 60:02d}",
                    "resources": option.output_resources(),
                }
            )
        return assignments

    def _extract_preference_summary(
        self,
        solver: cp_model.CpSolver,
    ) -> JsonObject:
        if not self.preference_pairs:
            return self._empty_preference_summary()

        total_weight = sum(
            int(pair["weight"]) for pair in self.preference_pairs
        )
        achieved_weight = sum(
            int(pair["weight"])
            for pair in self.preference_pairs
            if any(solver.Value(variable) == 1 for variable in pair["matching_vars"])
        )
        score = (achieved_weight / total_weight * 100) if total_weight else None
        return {
            "total_pairs": len(self.preference_pairs),
            "achieved_pairs": sum(
                1
                for pair in self.preference_pairs
                if any(
                    solver.Value(variable) == 1
                    for variable in pair["matching_vars"]
                )
            ),
            "total_weight": total_weight,
            "achieved_weight": achieved_weight,
            "score_percentage": score,
        }

    @staticmethod
    def _empty_preference_summary() -> JsonObject:
        return {
            "total_pairs": 0,
            "achieved_pairs": 0,
            "total_weight": 0,
            "achieved_weight": 0,
            "score_percentage": None,
            "message": "Tidak ada preference",
        }

    def _planning_dates(self) -> list[date]:
        total_days = (self.period_end - self.period_start).days
        return [
            self.period_start + timedelta(days=offset)
            for offset in range(total_days + 1)
        ]


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
