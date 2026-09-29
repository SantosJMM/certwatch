from datetime import datetime, timedelta, timezone
from pathlib import Path
import certwatch.discovery as discovery

def test_dynamic_discovery_inspects_every_lineage(tmp_path, monkeypatch):
    live=tmp_path/'live'; renewal=tmp_path/'renewal'; live.mkdir(); renewal.mkdir()
    for name in ('alpha.example','beta.example'):
        d=live/name; d.mkdir(); (d/'fullchain.pem').write_text('fixture'); (renewal/f'{name}.conf').write_text('renewal')
    def decoded(path):
        name=Path(path).parent.name
        return {'notAfter':(datetime.now(timezone.utc)+timedelta(days=40)).strftime('%b %d %H:%M:%S %Y GMT'),'subjectAltName':(('DNS',name),),'issuer':((('commonName','Test CA'),),)}
    monkeypatch.setattr(discovery.ssl._ssl,'_test_decode_cert',decoded)
    records,error=discovery.discover(live,renewal)
    assert error is None
    assert [r.lineage for r in records] == ['alpha.example','beta.example']
    assert all(r.renewal_config=='present' and r.status=='ok' for r in records)

def test_filters_and_broken_symlink_are_reported(tmp_path):
    live=tmp_path/'live'; live.mkdir(); renewal=tmp_path/'renewal'; renewal.mkdir()
    d=live/'broken.example'; d.mkdir(); (d/'fullchain.pem').symlink_to('../missing.pem')
    records,error=discovery.discover(live,renewal,include=('broken.*',))
    assert error is None and records[0].status=='critical' and records[0].local_file_state=='broken_symlink'
