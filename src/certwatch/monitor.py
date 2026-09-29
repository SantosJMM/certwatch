from __future__ import annotations
import argparse,json,os,socket
from datetime import datetime,timezone
from pathlib import Path
from .config import ConfigError,csv,integer,load
from .discovery import discover

def check(config):
    warn=integer(config,"WARN_DAYS",30); critical=integer(config,"CRITICAL_DAYS",7)
    if critical>warn: raise ConfigError("CRITICAL_DAYS must be less than or equal to WARN_DAYS")
    records,error=discover(Path(config.get("CERTBOT_LIVE_DIR","/etc/letsencrypt/live")),Path(config.get("CERTWATCH_RENEWAL_DIR","/etc/letsencrypt/renewal")),warn,critical,csv(config,"CERT_INCLUDE"),csv(config,"CERT_EXCLUDE"))
    severity="critical" if error or not records or any(x.status=="critical" for x in records) else "warning" if any(x.status=="warning" for x in records) else "ok"
    return {"server_id":config.get("SERVER_ID") or socket.getfqdn(),"server_label":config.get("SERVER_LABEL", ""),"checked_at":datetime.now(timezone.utc).isoformat(),"severity":severity,"discovery_error":error,"certificates":[x.public() for x in records]}

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); p.add_argument("--config",type=Path,default=Path(os.environ.get("CERTWATCH_CONFIG_PATH","/etc/certwatch/certwatch.env"))); a=p.parse_args(argv)
    try: print(json.dumps(check(load(a.config)),sort_keys=True)); return 0
    except ConfigError as exc: print(f"certwatch: {exc}",file=__import__('sys').stderr); return 3
if __name__=="__main__": raise SystemExit(main())
