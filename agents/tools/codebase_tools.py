"""Read-only codebase access for Designer and CTO agents."""
from __future__ import annotations
import asyncio
from pathlib import Path
from core.config import settings


def tool_definitions() -> list[dict]:
    return [
        {
            "name": "codebase_list",
            "description": "List files/folders in product codebase (read-only).",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string", "default": ""}},
                "required": [],
            },
        },
        {
            "name": "codebase_read",
            "description": "Read a file from product codebase. Max 50KB returned.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "codebase_grep",
            "description": "Search for a regex pattern in codebase. Returns matching file paths + line numbers.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "glob": {"type": "string", "description": "e.g. '**/*.tsx'"},
                },
                "required": ["pattern"],
            },
        },
    ]


def _resolve(path: str) -> Path | None:
    """Защита от выхода за пределы snapshot dir."""
    base = Path(settings.codebase_snapshot_dir).resolve()
    target = (base / path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target


async def execute(name: str, args: dict) -> str:
    if name == "codebase_list":
        p = _resolve(args.get("path", ""))
        if not p or not p.exists():
            return "Path not found"
        if p.is_file():
            return p.name
        items = sorted([f"{e.name}/" if e.is_dir() else e.name for e in p.iterdir() if not e.name.startswith(".")])
        return "\n".join(items[:200])

    if name == "codebase_read":
        p = _resolve(args["path"])
        if not p or not p.exists() or not p.is_file():
            return "File not found"
        try:
            data = p.read_text(encoding="utf-8")[:50_000]
            return data
        except Exception as e:
            return f"Read error: {e}"

    if name == "codebase_grep":
        base = Path(settings.codebase_snapshot_dir)
        if not base.exists():
            return "Codebase snapshot not available"
        pattern = args["pattern"]
        glob = args.get("glob", "**/*")
        proc = await asyncio.create_subprocess_exec(
            "grep", "-rn", "-E", pattern, "--include", glob.replace("**/", ""), str(base),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8", errors="replace")[:20_000] or "No matches"

    return f"Unknown codebase tool: {name}"
