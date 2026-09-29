from __future__ import annotations
from pathlib import Path

class ConfigError(RuntimeError): pass

def load(path: Path) -> dict[str, str]:
    try: lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc: raise ConfigError(f"cannot read configuration: {path}") from exc
    data: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"): continue
        if "=" not in raw: raise ConfigError("invalid configuration line")
        key, value = raw.split("=", 1); key = key.strip()
        if not key or not key.replace("_", "").isalnum(): raise ConfigError("invalid configuration key")
        data[key] = value.strip()
    return data

def integer(c: dict[str,str], key: str, default: int, minimum: int=0, maximum: int=3600) -> int:
    try: value=int(c.get(key, str(default)))
    except ValueError as exc: raise ConfigError(f"{key} must be an integer") from exc
    if not minimum <= value <= maximum: raise ConfigError(f"{key} outside safe range")
    return value

def enabled(c: dict[str,str], key: str, default=False) -> bool:
    value=c.get(key,str(default).lower()).lower()
    if value not in {"true","false"}: raise ConfigError(f"{key} must be true or false")
    return value == "true"

def csv(c: dict[str,str], key: str) -> tuple[str,...]:
    return tuple(x.strip() for x in c.get(key, "").split(",") if x.strip())
