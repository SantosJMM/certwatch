import json
import subprocess
import certwatch.agent as agent

def test_read_only_helper_uses_fixed_argv(monkeypatch):
    called={}
    def run(argv, **kwargs):
        called['argv']=argv
        return subprocess.CompletedProcess(argv,0,json.dumps({'server_id':'node','certificates':[{'lineage':'a','status':'ok','days_remaining':20}]}),'')
    monkeypatch.setattr(agent.subprocess,'run',run)
    assert 'a: ok' in agent.render_certs({'CERTWATCH_ACTION_HELPER':'/fixed/helper'})
    assert called['argv']==['/usr/bin/sudo','-n','/fixed/helper','read','certs']
