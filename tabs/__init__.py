def _status_icon(status: str) -> str:
    return {"correct": "✅", "incorrect": "❌", "uncertain": "⚠️"}.get(status, "❓")
