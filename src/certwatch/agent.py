"""Optional command-agent primitives; deployment controls Telegram polling separately."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
from .config import ConfigError, enabled, load

def read_certs(config: dict[str,str]) -> dict:
    helper=config.get("CERTWATCH_ACTION_HELPER","/usr/local/libexec/certwatch-action")
    run=subprocess.run(["/usr/bin/sudo","-n",helper,"read","certs"],text=True,capture_output=True,timeout=90,check=False)
    if run.returncode: raise ConfigError("certificate check failed")
    try: result=json.loads(run.stdout)
    except json.JSONDecodeError as exc: raise ConfigError("certificate helper returned invalid JSON") from exc
    if not isinstance(result,dict): raise ConfigError("certificate helper returned invalid JSON")
    return result

def render_certs(config:dict[str,str]) -> str:
    p=read_certs(config); lines=[f"Server: {p.get('server_id','unknown')}","Certificates:"]
    lines += [f"- {x.get('lineage','unknown')}: {x.get('status','unknown')}; days={x.get('days_remaining','unknown')}" for x in p.get('certificates',[]) if isinstance(x,dict)]
    return "\n".join(lines)

def main(argv=None):
    config=load(Path(os.environ.get("CERTWATCH_CONFIG_PATH","/etc/certwatch/certwatch.env")))
    if not enabled(config,"TELEGRAM_AGENT_ENABLED"): raise SystemExit("certwatch-agent: disabled by configuration")
    raise SystemExit("Use the systemd deployment template for long polling.")
