from typing import Any, Dict, Optional


class MetaMixin:
    def __init__(self, meta: Optional[Dict[Any, Any]] = None) -> None:
        self.meta = meta or {}
