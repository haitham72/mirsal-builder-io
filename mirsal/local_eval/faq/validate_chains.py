"""Validate seed imports, case contracts and activity fixtures without model or live writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
REPO=APP.parent
sys.path.insert(0,str(APP))
os.environ.update(MIRSAL_DB_WRITE='0',MIRSAL_SUPPORT_REPO='',MIRSAL_LLM_PROVIDER='none',MIRSAL_VISION_PROVIDER='none')
from mirsal.flow import faq,support,support_kb
from mirsal.store import sync

def contract():
    paths={p.relative_to(REPO/'faq').as_posix() for p in (REPO/'faq').rglob('*.md')}
    new=json.loads((HERE/'chain-sources.json').read_text(encoding='utf-8'))
    cases=json.loads((HERE/'cases.json').read_text(encoding='utf-8'))
    assert 20<=len(cases)<=30 and len({c['id'] for c in cases})==len(cases)
    unknowns=0; cited=set(); fixture_results=[]
    for c in cases:
        assert len(c['turns'])>=2
        for t in c['turns']:
            assert isinstance(t['user'],str) and t['user'].strip()
            e=t['expect']; assert e and not (set(e)-{'cites_faq','request','activity','need','no_answer'})
            if 'cites_faq' in e: assert e['cites_faq'] in paths; cited.add(e['cites_faq'])
            if 'request' in e: assert e['request'] in ('feature','access')
            if 'need' in e: assert e['need'] in ('clarify','screenshot')
            if 'no_answer' in e: assert e['no_answer'] is True; unknowns+=1
            if 'activity' in e: assert e['activity'] in ('job','batch') and 'fixture' in c
        if 'fixture' in c:
            f=c['fixture']
            with tempfile.TemporaryDirectory(prefix='faq-case-fixture-') as d:
                out=Path(d); os.environ['MIRSAL_OUT']=d
                assert not sync.enabled(out) and not support_kb._pg(out)
                (out/'jobs').mkdir()
                for j in f['jobs']:
                    assert j['id'].startswith('J') and j['request']['user'] in ('u1','u2')
                    (out/'jobs'/f"{j['id']}.json").write_text(json.dumps(j),encoding='utf-8')
                for b in f['batches']:
                    p=out/b['generation_id']; (p/'slices').mkdir(parents=True)
                    (p/'result.json').write_text(json.dumps(b),encoding='utf-8')
                hits=support.activity(out,f['user'],' '.join(t['user'] for t in c['turns']))
                assert not any(h['id']=='J005' for h in hits)
                for t in c['turns']:
                    if 'activity' in t['expect']:
                        assert any(h['ref']['type']==t['expect']['activity'] for h in hits)
                fixture_results.append(dict(case=c['id'],visible_ids=[h['id'] for h in hits],foreign_job_hidden=True))
    assert unknowns>=5
    assert {e['path'] for e in new}<=paths
    for p in (REPO/'faq').rglob('*.md'):
        s=faq.parse_seed(p.read_text(encoding='utf-8'))
        assert s['category']==p.parent.name and bool(s['screen'])==bool(s['looks_like'])
    return dict(chains=len(cases),turns=sum(len(c['turns']) for c in cases),no_answer_turns=unknowns,
                referenced_faqs=len(cited),new_entries=len(new),total_entries=len(paths),fixtures=fixture_results)

def main():
    result=contract(); result['imports']={}
    with tempfile.TemporaryDirectory(prefix='faq-chains-drafts-') as d, tempfile.TemporaryDirectory(prefix='faq-chains-published-') as pub:
        def cli(out,publish=False):
            os.environ['MIRSAL_OUT']=out
            args=[sys.executable,'-m','mirsal','support','import-faq','--repo',str(REPO/'faq'),'--json']
            if publish: args.append('--publish')
            r=subprocess.run(args,cwd=APP,env=dict(os.environ),capture_output=True,text=True,encoding='utf-8')
            if r.returncode: raise RuntimeError(r.stderr or r.stdout)
            return json.loads(r.stdout)
        first=cli(d); second=cli(d); n=result['total_entries']
        assert len(first['created'])==n and not first['updated'] and not first['skipped']
        assert second['unchanged']==n and not second['created'] and not second['updated'] and not second['skipped']
        assert not support_kb.search(Path(d),'How do I read a private reply from support?','member')['hits']
        published=cli(pub,True)
        assert len(published['created'])==n and not published['skipped']
        result['imports']=dict(first=first,second=second,temporary_publish=published)
        result['draft_hits']=0
        mapping={faq.read(Path(pub),r['id'])['seed']['path']:r['id'] for r in faq.listing(Path(pub))}
        direct=[]
        for e in json.loads((HERE/'chain-sources.json').read_text(encoding='utf-8')):
            hits=support_kb.search(Path(pub),e['question'],'member')
            expected=mapping[e['path']]
            direct.append(dict(path=e['path'],question=e['question'],expected_id=expected,
                               first_id=hits['hits'][0]['id'] if hits['hits'] else None,mode=hits['mode'],enough=hits['enough'],
                               passed=bool(hits['hits'] and hits['hits'][0]['id']==expected)))
        result['new_question_retrieval']=direct
        result['new_top1']=sum(x['passed'] for x in direct)
        regression=[]
        for t in json.loads((HERE/'questions.json').read_text(encoding='utf-8')):
            hit=support_kb.search(Path(pub),t['query'],'member'); expected=mapping[t['expected_path']]
            regression.append(dict(**t,expected_id=expected,first_id=hit['hits'][0]['id'] if hit['hits'] else None,
                                   passed=bool(hit['hits'] and hit['hits'][0]['id']==expected),enough=hit['enough'],mode=hit['mode']))
        result['original_query_regression']=regression
        result['original_top1']=sum(x['passed'] for x in regression)
    result['isolation']=dict(database_write='0',corpus='FAQ only',text_provider='none',vision_provider='none',output='automatically removed temporary directories')
    result['end_to_end_cases_run']=False
    (HERE/'chain-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('chains','turns','no_answer_turns','new_entries','total_entries','new_top1','original_top1')}))
    for x in direct+regression:
        if not x['passed']: print(json.dumps(x,ensure_ascii=False))

if __name__=='__main__': main()
