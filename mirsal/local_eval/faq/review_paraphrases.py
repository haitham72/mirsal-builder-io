import json
from pathlib import Path

here=Path(__file__).resolve().parent
record=json.loads((here/'chain-paraphrases.json').read_text(encoding='utf-8'))
cases=json.loads((here/'cases.json').read_text(encoding='utf-8'))
by_id={c['id']:c for c in cases}
accepted=[]
for d in record['drafts']:
    if d['id']=='blocked-sticker-to-external-edit-feature': continue
    by_id[d['id']]['turns'][0]['user']=d['text']; accepted.append(d['id'])
record.update(applied=True,accepted_ids=accepted,rejected=[dict(id='blocked-sticker-to-external-edit-feature',reason='Changed touching the boundary to extending beyond it; retained the precise original wording.')])
for name,value in [('cases.json',cases),('chain-paraphrases.json',record)]:
    (here/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Applied 9 reviewed paraphrases; retained 1 original question.')
