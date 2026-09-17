from __future__ import annotations

import json
from pathlib import Path

from .schedovyn_solver_prototype import parse_args, PilotSolver

def main() -> None:
    args = parse_args()
    snapshot_path = Path(args.input)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    result = PilotSolver(snapshot).solve()
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
