import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace

repo = Path.cwd()
(repo / 'output/playwright').mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo / 'mirsal'))
for key, value in {'MIRSAL_NO_REAL_CLI': '1', 'MIRSAL_LLM_PROVIDER': 'none',
                   'MIRSAL_AGENT_PROVIDER': 'none', 'MIRSAL_VISION_PROVIDER': 'none',
                   'MIRSAL_DB_WRITE': '0', 'MIRSAL_TRACE': 'none',
                   'LANGSMITH_TRACING': 'false'}.items():
    os.environ[key] = value
root = Path(tempfile.mkdtemp(prefix='mirsal-final-acceptance-'))
out = root / 'outcopy'
out.mkdir()
src = next((repo / 'mirsal/out').glob('G146-*'))
shutil.copytree(src, out / src.name)
# No jobs, accounts, chats, library or configuration from the real output.
from tests.synth import make_video
from mirsal.engine.config import EngineConfig
from mirsal.flow import imports as im
video = root / 'synthetic-3x3.mp4'
make_video(video, frames=36)
# Reserve the fixture's requested id without importing any other real batch.
(out / 'G155-acceptance-id-reservation').mkdir()
c = SimpleNamespace(out=out, inp=root / 'inputs', lock=threading.Lock(),
                    cfg=EngineConfig(min_sheet_px=256), pace=0)
status, result = im.import_file(c, {'id': 'local'}, video.name, video.read_bytes(), grid='3x3')
with c.lock:
    pass
(root / 'fixture.json').write_text(json.dumps({'status': status, 'result': result}))
(repo / 'output/playwright/scratch.txt').write_text(str(root))
config = {'browser': {'browserName': 'chromium', 'launchOptions': {'headless': True, 'channel': 'chrome'},
                     'contextOptions': {'viewport': {'width': 1440, 'height': 900}, 'deviceScaleFactor': 1}},
          'outputDir': str(root / 'browser')}
(root / 'browser.json').write_text(json.dumps(config))
print(root, result)
