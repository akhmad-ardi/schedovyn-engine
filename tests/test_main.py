import json
from pathlib import Path

from solver.pilot_solver import PilotSolver


def test_solver():
    snapshot_path = Path("data/bengkel/Snapshot-input-bengkel-final.json")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    result = PilotSolver(snapshot).solve()

    # ── 1. Top-level structure ────────────────────────────────────────────
    assert result["schema_version"] == "pilot-training-solver-result-1.0.0"
    assert result["dataset_id"] == snapshot.get("dataset_id")
    assert result["input_revision"] == snapshot.get("input_revision")

    # ── 2. Solver berhasil menemukan solusi (Optimal atau Feasible) ───────
    assert result["solution_status"] in ("Optimal", "Feasible"), (
        f"Solver gagal: solution_status={result['solution_status']!r}, "
        f"solver_status={result.get('solver_status')!r}"
    )

    # ── 3. Tidak ada occurrence yang tidak terassign ──────────────────────
    assert result["unassigned_occurrences"] == [], (
        f"Occurrence tidak terassign: {result['unassigned_occurrences']}"
    )

    # ── 4. Setiap occurrence dalam snapshot muncul tepat sekali ──────────
    expected_occurrence_ids = {occ["id"] for occ in snapshot.get("occurrences", [])}
    assigned_ids = [a["occurrence_id"] for a in result["assignments"]]
    assert set(assigned_ids) == expected_occurrence_ids, (
        f"Assigned IDs tidak cocok.\n"
        f"  Kurang : {expected_occurrence_ids - set(assigned_ids)}\n"
        f"  Lebih  : {set(assigned_ids) - expected_occurrence_ids}"
    )
    assert len(assigned_ids) == len(set(assigned_ids)), (
        "Terdapat duplikat occurrence_id dalam assignments"
    )

    # ── 5. Setiap assignment memiliki field yang wajib ada ────────────────
    for assignment in result["assignments"]:
        oid = assignment["occurrence_id"]
        assert "date" in assignment, f"Assignment {oid} tidak punya 'date'"
        assert "start" in assignment, f"Assignment {oid} tidak punya 'start'"
        assert "end" in assignment, f"Assignment {oid} tidak punya 'end'"
        assert "resources" in assignment, f"Assignment {oid} tidak punya 'resources'"
        assert isinstance(assignment["resources"], dict), (
            f"Assignment {oid}: 'resources' harus berupa dict"
        )
        assert assignment["resources"], (
            f"Assignment {oid}: 'resources' tidak boleh kosong"
        )

    # ── 6. Preference score ───────────────────────────────────────────────
    preference = result["preference"]
    assert preference["score_percentage"] == 100.0, (
        f"Preference score tidak 100%: {preference['score_percentage']}% "
        f"({preference['achieved_pairs']}/{preference['total_pairs']} pairs, "
        f"weight {preference['achieved_weight']}/{preference['total_weight']})"
    )

    # ── 7. Solver stats tersedia (nilai runtime tidak divalidasi) ─────────
    solver_stats = result["solver"]
    for key in ("objective_value", "best_objective_bound", "wall_time_seconds",
                "num_conflicts", "num_branches"):
        assert key in solver_stats, f"solver_stats tidak punya key '{key}'"