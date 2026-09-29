from __future__ import annotations
import fnmatch, ssl
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

@dataclass(frozen=True)
class Certificate:
    lineage: str; san_domains: tuple[str,...]; issuer: str|None; expiry_utc: str|None
    days_remaining: int|None; local_file_state: str; renewal_config: str; status: str; error: str|None=None
    def public(self): return asdict(self)

def _status(days, error, warn, critical):
    return "critical" if error or days is None or days <= critical else "warning" if days <= warn else "ok"

def _selected(name, sans, include, exclude):
    candidates=(name,)+sans
    match=lambda ps:any(fnmatch.fnmatchcase(x,p) for x in candidates for p in ps)
    return (not include or match(include)) and not match(exclude)

def inspect(fullchain: Path, lineage: str, renewal: Path, warn: int, critical: int) -> Certificate:
    renewal_state="present" if (renewal/f"{lineage}.conf").is_file() else "missing"
    if fullchain.is_symlink():
        try: state=f"symlink->{fullchain.resolve(strict=True)}"
        except OSError: return Certificate(lineage,(),None,None,None,"broken_symlink",renewal_state,"critical","fullchain symlink is broken")
    elif fullchain.is_file(): state="regular_file"
    else: return Certificate(lineage,(),None,None,None,"missing",renewal_state,"critical","fullchain.pem is missing")
    try:
        d=ssl._ssl._test_decode_cert(str(fullchain.resolve()))
        expiry=datetime.strptime(d["notAfter"],"%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        sans=tuple(v for k,v in d.get("subjectAltName",()) if k=="DNS")
        issuer=", ".join(f"{k}={v}" for rdn in d.get("issuer",()) for k,v in rdn) or None
        days=(expiry-datetime.now(timezone.utc)).days
        return Certificate(lineage,sans,issuer,expiry.isoformat(),days,state,renewal_state,_status(days,None,warn,critical))
    except Exception: return Certificate(lineage,(),None,None,None,state,renewal_state,"critical","certificate decode failed")

def discover(live: Path, renewal: Path, warn: int=30, critical: int=7, include=(), exclude=()):
    if not live.is_dir(): return (), "CERTBOT_LIVE_DIR is missing or unreadable"
    try: entries=sorted(live.iterdir(),key=lambda p:p.name)
    except OSError: return (), "unable to enumerate CERTBOT_LIVE_DIR"
    records=[]
    for directory in entries:
        if not directory.is_dir(): continue
        fullchain=directory/"fullchain.pem"
        if not (fullchain.exists() or fullchain.is_symlink()): continue
        record=inspect(fullchain,directory.name,renewal,warn,critical)
        if _selected(record.lineage,record.san_domains,include,exclude): records.append(record)
    return tuple(records),None
