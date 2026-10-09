"""The AI chat in Telegram (services/tg_chat.py): a real console, the Telegram calls recorded instead of sent; no network, no model, no provider."""
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
from mirsal.engine.config import EngineConfig
from mirsal.generation import higgsfield as hf
from tests import synth

HAITHAM, STRANGER = "777", "555"


class TelegramChatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from mirsal.console.server import serve
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {"MIRSAL_API_TOKEN": "tg-test-owner", "MIRSAL_ADMIN_BOT": "1"})
        cls.hf = patch.object(hf, "available", return_value=False)
        cls.env.start(); cls.hf.start()
        cls.srv, cls.c = serve(Path(cls.tmp.name) / "out", Path(cls.tmp.name) / "in", 0, cfg=EngineConfig(min_sheet_px=256), block=False, stdlib=False)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        (cls.c.out / "telegram.json").write_text(json.dumps({"token": "123:abc", "user_id": HAITHAM, "bot": "mirsal_bot"}), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.c.wait_chat(); cls.c.wait_jobs()
        cls.srv.shutdown(); cls.c.release_writer()
        cls.hf.stop(); cls.env.stop(); cls.tmp.cleanup()

    def setUp(self):
        self.calls = []
        self.lock = threading.Lock()

        def fake(token, method, fields, files=None, timeout=60):
            with self.lock:
                self.calls.append((method, fields, sorted((files or {}).keys())))
                return {"message_id": len(self.calls)}
        self.p = patch("mirsal.services.telegram._call", fake)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def update(self, who, text=None, data=None, mid=1):
        from mirsal.services import admin_bot
        frm = {"id": int(who), "first_name": "Sara" if who == STRANGER else "Haitham", "username": "sara" if who == STRANGER else "h"}
        if data:
            u = {"update_id": 1, "callback_query": {"id": "q", "from": frm, "data": data, "message": {"message_id": mid, "chat": {"id": int(who), "type": "private"}}}}
        else:
            u = {"update_id": 1, "message": {"message_id": mid, "from": frm, "chat": {"id": int(who), "type": "private"}, "text": text}}
        admin_bot.handle_update(self.c, u)

    def sent(self, method="sendMessage", chat=None):
        return [f for m, f, _ in self.calls if m == method and (chat is None or str(f.get("chat_id")) == str(chat))]

    def buttons(self, fields):
        return [b for row in ((fields.get("reply_markup") or {}).get("inline_keyboard") or []) for b in row]

    def wait_quiet(self, chat, seconds=20):
        from mirsal.services import tg_chat
        end = time.time() + seconds
        while time.time() < end:
            t = tg_chat._FOLLOW.get(str(chat))
            if not t or not t.is_alive():
                return
            time.sleep(0.1)

    def test_a_stranger_gets_an_account_with_no_credits_and_haitham_a_card(self):
        self.update(STRANGER, "/start")
        people = json.loads((self.c.out / "telegram_chats.json").read_text(encoding="utf-8"))["people"]
        uid = people[STRANGER]["user"]
        u = self.c.users.get(uid)
        self.assertEqual((u["role"], u["credits_left"]), ("member", 0), "an account without a balance would spend without limit")
        card = [f for f in self.sent(chat=HAITHAM) if "New Telegram user: Sara" in f["text"]]
        self.assertEqual(len(card), 1)
        self.assertIn(f"u:{uid}:credits", [b["callback_data"] for b in self.buttons(card[0])])
        self.assertIn("Welcome to Mirsal", self.sent(chat=STRANGER)[-1]["text"])
        self.update(STRANGER, "/start")
        self.assertEqual(len([f for f in self.sent(chat=HAITHAM) if "New Telegram user" in f["text"]]), 1, "one card per person, never per message")
        self.update(HAITHAM, data=f"u:{uid}:credits")
        self.assertEqual(self.c.users.get(uid)["credits_left"], 10, "Haitham's +10 tap is the existing admin action")

    def test_a_chat_starts_on_the_telegram_defaults_and_model_changes_them_with_buttons(self):
        from mirsal.services import tg_chat
        self.update(HAITHAM, "/model")
        card = self.sent(chat=HAITHAM)[-1]
        labels = [b["text"] for b in self.buttons(card)]
        self.assertEqual(labels, ["🖼 Nano Banana 2", "🎞 Grok Imagine 1.5 Lite", "🎨 " + next(s["label"] for s in __import__("mirsal.generation.styles", fromlist=["x"]).PRESETS if s["id"] == "glossy_3d"), "🤖 gpt-4o", "🧭 Emojis"])
        self.update(HAITHAM, data=self.buttons(card)[0]["callback_data"])                    # open the image list
        listing = [f for m, f, _ in self.calls if m == "editMessageText"][-1]
        pick = next(b for b in self.buttons(listing) if b["text"] == "Seedream 5.0 Pro")
        self.update(HAITHAM, data=pick["callback_data"])
        sid = tg_chat._chat(self.c.out, HAITHAM)["sid"]
        settings = self.c.chat_parts({"id": "local", "role": "owner"})[0].load(sid)["settings"]
        self.assertEqual(settings["models"], {"image": "seedream_v5_pro", "video": "grok_video_v15_lite", "ai": "gpt-4o"})
        self.assertEqual(settings["style_id"], "glossy_3d")
        _, tools, _, _ = self.c.chat_parts({"id": "local", "role": "owner", "can_spend": True}, sid)
        self.assertEqual(tools.models["image"], "seedream_v5_pro", "the chat's tools send the chat's own model")

    def test_stage_is_a_fifth_row_and_its_own_command(self):
        """plan.md Step 2: /model carries the stage (a new chat is on Emojis), /stage opens the four choices, a pick saves settings.stage and makes no turn."""
        from mirsal.services import tg_chat
        self.update(HAITHAM, "/new")
        self.update(HAITHAM, "/stage")
        card = self.sent(chat=HAITHAM)[-1]
        labels = [b["text"] for b in self.buttons(card)]
        self.assertEqual(labels, ["Prompt · plan only, free", "✓ Emojis · sheet and stickers", "Animation · + animation", "Export · + pack and send", "‹ Back"])
        self.update(HAITHAM, data=self.buttons(card)[2]["callback_data"])
        sid = tg_chat._chat(self.c.out, HAITHAM)["sid"]
        sess = self.c.chat_parts({"id": "local", "role": "owner"})[0].load(sid)
        self.assertEqual((sess["settings"]["stage"], sess["messages"]), ("animation", []), "a pick is a setting, never a turn")
        self.assertEqual(self.buttons([f for m, f, _ in self.calls if m == "editMessageText"][-1])[-1]["text"], "🧭 Animation")

    def test_a_message_is_a_turn_of_the_same_agent_and_its_reply_comes_back(self):
        from mirsal.services import tg_chat
        self.update(HAITHAM, "/new")
        self.update(HAITHAM, "hello")
        self.c.wait_chat()
        self.wait_quiet(HAITHAM)
        sid = tg_chat._chat(self.c.out, HAITHAM)["sid"]
        msgs = self.c.chat_parts({"id": "local", "role": "owner"})[0].load(sid)["messages"]
        self.assertEqual(msgs[0]["text"], "hello")
        self.assertTrue(any(m["role"] == "assistant" for m in msgs))
        replies = [f["text"] for f in self.sent(chat=HAITHAM)]
        self.assertTrue(any(r and "Welcome" not in r and "new chat" not in r for r in replies), replies)
        n = len(self.sent(chat=HAITHAM))
        tg_chat.render(self.c, HAITHAM, {"id": "local", "role": "owner", "can_spend": True}, sid)
        self.assertEqual(len(self.sent(chat=HAITHAM)), n, "a part is sent once, however often the chat is polled")

    def test_a_batch_arrives_as_one_album_once(self):
        from mirsal.flow import imports as im
        from mirsal.services import tg_chat
        data = cv2.imencode(".png", cv2.cvtColor(synth.make_sheet(), cv2.COLOR_RGB2BGR))[1].tobytes()
        _, j = im.import_file(self.c, {"id": "local"}, "bear.png", data)
        self.c.wait_jobs()
        gid = f"G{j['id']:03d}"
        _, tools, _, _ = self.c.chat_parts({"id": "local", "role": "owner", "can_spend": True})
        card = {"type": "generation", "generation": gid, "data": tools.generation(gid)}
        self.assertFalse(tg_chat._gen_parts(self.c, HAITHAM, card))
        albums = [(f, files) for m, f, files in self.calls if m == "sendMediaGroup"]
        self.assertEqual(len(albums), 1)
        media = json.loads(albums[0][0]["media"]) if isinstance(albums[0][0]["media"], str) else albums[0][0]["media"]
        self.assertEqual(len(media), len(albums[0][1]))
        self.assertIn(gid, media[0]["caption"])
        tg_chat._gen_parts(self.c, HAITHAM, card)
        self.assertEqual(len([1 for m, _, _ in self.calls if m == "sendMediaGroup"]), 1, "never twice")

    def test_a_blocked_sticker_carries_use_it_anyway(self):
        from mirsal.services import tg_chat
        gid, s = "G900", {"index": 3, "status": "FAILED", "reason": "inside_cell", "png": None}
        tg_chat._blocked(self.c, HAITHAM, gid, s, "still", {"can": [3], "why": {"3": "the character touches its cell"}})
        msg = self.sent(chat=HAITHAM)[-1]
        self.assertIn("the character touches its cell", msg["text"])
        self.assertEqual([b["text"] for b in self.buttons(msg)], ["Use it anyway"])
        tg_chat._blocked(self.c, HAITHAM, gid, {**s, "index": 4}, "still", {"can": [], "final": {"4": "nothing was cut here"}})
        msg = self.sent(chat=HAITHAM)[-1]
        self.assertIn("nothing was cut here", msg["text"])
        self.assertEqual(self.buttons(msg), [], "a final block says why instead")

    def test_a_stale_button_answers_in_words(self):
        self.update(HAITHAM, data="c:deadbeef00")
        ans = [f for m, f, _ in self.calls if m == "answerCallbackQuery"][-1]
        self.assertIn("too old", ans["text"])

    def test_a_pinned_ai_model_is_what_the_chat_uses(self):
        from mirsal.agent import brain
        from mirsal.services import llm
        with patch.dict(os.environ, {"MIRSAL_AGENT_PROVIDER": "auto", "OPENAI_API_KEY": "sk-test"}):
            tok = llm.FORCE.set({"model": "gpt-4o"})
            try:
                self.assertEqual(brain.target(), {"provider": "openai", "model": "gpt-4o"})
            finally:
                llm.FORCE.reset(tok)
        self.assertEqual(llm.provider(), "none", "the suite's MIRSAL_LLM_PROVIDER=none always wins")


if __name__ == "__main__":
    unittest.main()
