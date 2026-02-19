from __future__ import annotations

from pathlib import Path


class SQLQueryLoader:
    """
    Parse SQL files containing named query sections:
    - -- query_name: name
    - -- @query: name
    """

    def __init__(self, sql_file: str | Path) -> None:
        self.sql_file = Path(sql_file)
        self.queries: dict[str, str] = {}
        self._parse()

    def _parse(self) -> None:
        if not self.sql_file.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_file}")

        current_name: str | None = None
        current_lines: list[str] = []

        for line in self.sql_file.read_text(encoding="utf-8").splitlines():
            marker = None
            if "-- query_name:" in line:
                marker = line.split("query_name:", 1)[1].strip()
            elif "-- @query:" in line:
                marker = line.split("@query:", 1)[1].strip()

            if marker is not None:
                if current_name and current_lines:
                    self.queries[current_name] = "\n".join(current_lines).strip()
                current_name = marker
                current_lines = []
                continue

            if current_name is not None and not line.strip().startswith("--"):
                current_lines.append(line)

        if current_name and current_lines:
            self.queries[current_name] = "\n".join(current_lines).strip()

    def get_query(self, name: str) -> str:
        if name not in self.queries:
            available = ", ".join(self.queries.keys())
            raise KeyError(f"Query '{name}' not found. Available: {available}")
        return self.queries[name]

    def list_queries(self) -> list[str]:
        return list(self.queries.keys())

    def has_query(self, name: str) -> bool:
        return name in self.queries
