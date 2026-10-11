"""Cloud catalog/selection and Luna routing on fake responses only."""
import os
import io
import json
import tempfile
import unittest
from unittest import mock

from mirsal.services import embed, llm, llm_catalog as catalog
from mirsal.agent import brain
from mirsal.vision import judge


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.env = mock.patch.dict(os.environ, {
            "MIRSAL_OUT": self.td.name, "MIRSAL_LLM_PROVIDER": "openai", "MIRSAL_AGENT_PROVIDER": "auto",
            "MIRSAL_VISION_PROVIDER": "auto", "MIRSAL_CLOUD_URL": "https://router.example/v1",
            "NARAROUTER_API_KEY": "router-key", "OPENAI_API_KEY": "direct-key",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        p = mock.patch.object(llm, "_ENV_LOADED", True)
        p.start(); self.addCleanup(p.stop)
        p = mock.patch.object(llm, "list_local_models", return_value=["qwen:2"])
        p.start(); self.addCleanup(p.stop)
        p = mock.patch.object(llm, "local_reachable", return_value=False)
        p.start(); self.addCleanup(p.stop)
        catalog._CACHE.clear()
        llm._sticky.update(prov=None, until=0)
        self.addCleanup(catalog._CACHE.clear)
        token = llm.FORCE.set(None)
        self.addCleanup(llm.FORCE.reset, token)

    def fake_list(self, url, key):
        ids = [*catalog.NARAROUTER_VISION, "gpt-5.6-luna", "jev", "laguna-s-2.1", "nemotron-3-ultra-free", "text-embedding-3-small"]
        if key == "direct-key":
            ids = list(catalog.OPENAI_VISION)
        return {"data": [{"id": mid} for mid in ids]}

    def test_all_planned_models_are_listed_and_text_only_models_are_filtered(self):
        with mock.patch.object(catalog, "_fetch", side_effect=self.fake_list) as fetch:
            groups = catalog.groups()
            self.assertEqual([r["model"] for r in groups["nararouter"]], list(catalog.NARAROUTER_VISION))
            self.assertEqual(groups["local"][0]["id"], "local:qwen:2")
            self.assertEqual(groups["openai"][0]["id"], "openai:gpt-5.6-luna")
            self.assertNotIn("gpt-5.6-luna", [r["model"] for r in groups["nararouter"]])
            catalog.groups()
            self.assertEqual(fetch.call_count, 2, "one cached read per cloud provider")

    def test_unknown_and_removed_models_cannot_be_selected(self):
        with mock.patch.object(catalog, "_fetch", return_value={"data": [{"id": "gpt-5.6-luna"}]}):
            with self.assertRaises(llm.LLMError):
                catalog.validate("nararouter:jev")
            with self.assertRaises(llm.LLMError):
                catalog.validate("nararouter:mimo-v2.6-flash-free")
            self.assertEqual(catalog.validate("nararouter:gpt-5.6-luna"), "openai:gpt-5.6-luna")

    def test_catalog_authentication_is_separate_and_refreshes_when_a_key_changes(self):
        with mock.patch.object(catalog, "_fetch", side_effect=self.fake_list) as fetch:
            catalog.groups()
            self.assertEqual(fetch.call_args_list, [
                mock.call("https://router.example/v1", "router-key"),
                mock.call("https://api.openai.com/v1", "direct-key")])
            os.environ["NARAROUTER_API_KEY"] = "rotated-router-key"
            catalog.groups()
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual(fetch.call_args, mock.call("https://router.example/v1", "rotated-router-key"))

    def test_a_missing_provider_key_never_borrows_the_other_credential(self):
        for provider, key_name, selected in (
            ("nararouter", "NARAROUTER_API_KEY", "nararouter:agnes-2.5-flash"),
            ("openai", "OPENAI_API_KEY", "openai:gpt-5.6-luna"),
        ):
            with self.subTest(provider=provider), mock.patch.dict(os.environ):
                os.environ.pop(key_name)
                os.environ["MIRSAL_LLM_MODEL"] = selected
                with mock.patch.object(catalog, "_fetch") as fetch, mock.patch.object(llm, "_post") as post:
                    self.assertEqual(catalog.cloud_models(provider), [])
                    self.assertFalse(llm.cloud_available())
                    self.assertIn(key_name, llm.availability(probe=False)["cloud"]["why"])
                    with self.assertRaisesRegex(llm.LLMError, key_name):
                        catalog.validate(selected)
                    with self.assertRaisesRegex(llm.LLMError, key_name):
                        llm._complete_on("openai", "s", "u", model_=selected)
                    fetch.assert_not_called()
                    post.assert_not_called()

    def test_cloud_completions_bind_each_key_to_its_provider_endpoint(self):
        answer = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        for selected, url, key in (
            ("nararouter:agnes-2.5-flash", "https://router.example/v1", "router-key"),
            ("openai:gpt-4.1-mini", "https://api.openai.com/v1", "direct-key"),
        ):
            with self.subTest(model=selected), mock.patch.object(llm, "_post", return_value=answer) as post:
                llm._complete_on("openai", "s", "u", model_=selected, base_url="https://other.example/v1")
                self.assertEqual((post.call_args.args[0], post.call_args.args[2]), (url + "/chat/completions", key))
        os.environ.pop("OPENAI_API_KEY")
        os.environ["MIRSAL_CLOUD_URL"] = "https://api.openai.com/v1"
        self.assertIsNone(catalog.endpoint("openai")[1])
        self.assertIsNone(catalog.endpoint("nararouter")[1], "a router key must not be sent to the official URL")

    def test_cloud_embeddings_use_only_the_configured_endpoint_credential(self):
        answer = {"data": [{"index": 0, "embedding": [0.0] * embed.DIMS}]}
        for url, key_name, key in (
            ("https://router.example/v1", "NARAROUTER_API_KEY", "router-key"),
            ("https://api.openai.com/v1", "OPENAI_API_KEY", "direct-key"),
        ):
            with self.subTest(url=url), mock.patch.dict(os.environ, {"MIRSAL_CLOUD_URL": url}):
                b = embed.backend()
                self.assertEqual(b, {"provider": "openai", "model": embed.OPENAI_EMBED_MODEL})
                with mock.patch.object(embed, "_post", return_value=answer) as post:
                    self.assertEqual(len(embed._call(["text"], b)[0]), embed.DIMS)
                    self.assertEqual((post.call_args.args[0], post.call_args.args[2]), (url + "/embeddings", key))
                with mock.patch.object(embed, "_post", side_effect=OSError("denied " + key)):
                    with self.assertRaises(embed.EmbedError) as raised:
                        embed._call(["text"], b)
                    self.assertNotIn(key, str(raised.exception))
                os.environ.pop(key_name)
                self.assertEqual(embed.backend()["provider"], "none")
                with mock.patch.object(embed, "_post") as post:
                    with self.assertRaisesRegex(embed.EmbedError, key_name):
                        embed._call(["text"], b)
                    post.assert_not_called()

    def test_provider_none_never_fetches_cloud_catalogs(self):
        os.environ["MIRSAL_LLM_PROVIDER"] = "none"
        with mock.patch.object(catalog, "_fetch", side_effect=AssertionError("network disabled")):
            self.assertEqual(catalog.cloud_models("nararouter"), [])

    def test_luna_default_uses_official_openai_and_high_reasoning(self):
        self.assertEqual(llm.cloud_model(), "openai:gpt-5.6-luna")
        sent = []
        def post(url, body, key, timeout):
            sent.append((url, body, key))
            return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        with mock.patch.object(llm, "_post", side_effect=post):
            llm._complete_on("openai", "s", "u")
            llm._complete_on("openai", "s", "u", model_="openai:gpt-5.6-luna", images=[b"image"])
            llm._complete_on("local", "s", "u", model_="local:qwen:2")
        self.assertEqual([(url, key) for url, _, key in sent], [
            ("https://api.openai.com/v1/chat/completions", "direct-key"),
            ("https://api.openai.com/v1/chat/completions", "direct-key"),
            (llm.LOCAL_URL + "/chat/completions", None)])
        self.assertEqual(sent[0][1]["model"], "gpt-5.6-luna")
        self.assertEqual(sent[0][1]["reasoning_effort"], "high")
        self.assertGreaterEqual(sent[0][1]["max_completion_tokens"], 8192)
        self.assertNotIn("temperature", sent[0][1])
        self.assertEqual(sent[2][1]["model"], "qwen:2")

    def test_image_requests_reject_text_only_before_sending(self):
        with mock.patch.object(llm, "_post", side_effect=AssertionError("must not send")):
            with self.assertRaisesRegex(llm.LLMError, "image-capable"):
                llm._complete_on("openai", "s", "u", model_="nararouter:jev", images=[b"image"])

    def test_existing_luna_ids_route_to_openai_and_need_its_own_key(self):
        for value in ("gpt-5.6-luna", "nararouter:gpt-5.6-luna", "openai:gpt-5.6-luna"):
            with self.subTest(value=value):
                self.assertEqual(catalog.split_model(value), ("openai", "gpt-5.6-luna"))
                llm.FORCE.set({"model": value})
                self.assertEqual(brain.target()["model"], "openai:gpt-5.6-luna")
                self.assertEqual(judge.target()["model"], "openai:gpt-5.6-luna")
        os.environ.pop("OPENAI_API_KEY")
        self.assertEqual(llm.forced_provider(), "none", "the router key is never used as an official OpenAI key")
        with self.assertRaisesRegex(llm.LLMError, "OPENAI_API_KEY"):
            catalog.validate("nararouter:gpt-5.6-luna")

    def test_luna_high_and_official_endpoint_survive_max_env_and_optional_parameter_retry(self):
        import urllib.error
        os.environ["MIRSAL_CLOUD_REASONING"] = "max"
        error = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 400, "bad format", {},
                                       io.BytesIO(b'{"error":{"message":"response_format unsupported"}}'))
        answer = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        with mock.patch.object(llm, "_post", side_effect=[error, answer]) as post:
            llm._complete_on("openai", "s", "u", model_="nararouter:gpt-5.6-luna", json_mode=True,
                             base_url="https://router.example/v1", max_tokens=400)
            self.assertEqual(post.call_count, 2)
            for call in post.call_args_list:
                url, body, key, _ = call.args
                self.assertEqual((url, key), ("https://api.openai.com/v1/chat/completions", "direct-key"))
                self.assertEqual(body["reasoning_effort"], "high")
                self.assertEqual(body["max_completion_tokens"], 8192)
            self.assertNotIn("response_format", post.call_args_list[-1].args[1])

    def test_saved_selection_reaches_chat_and_vision_and_can_return_to_default(self):
        with mock.patch.object(catalog, "_fetch", side_effect=self.fake_list):
            llm.set_model("nararouter:agnes-3-flash")
            self.assertEqual(llm.cloud_model(), "nararouter:agnes-3-flash")
            self.assertEqual(brain.target()["model"], "nararouter:agnes-3-flash")
            self.assertEqual(judge.target()["model"], "nararouter:agnes-3-flash")
            llm._write_pref_file(cloud_model="")
            self.assertEqual(llm.cloud_model(), "openai:gpt-5.6-luna")
        llm.FORCE.set({"model": "local:qwen:2"})
        self.assertEqual(brain.target(), {"provider": "local", "model": "local:qwen:2"})
        self.assertEqual(judge.target()["model"], "local:qwen:2")

    def test_explicit_vision_override_and_existing_env_model_are_kept(self):
        os.environ["MIRSAL_LLM_MODEL"] = "mimo-v2.6-flash"
        os.environ["MIRSAL_VISION_OPENAI_MODEL"] = "agnes-2.5-flash"
        self.assertEqual(llm.cloud_model(), "mimo-v2.6-flash")
        self.assertEqual(judge.target()["model"], "agnes-2.5-flash")
        llm.FORCE.set({"model": "nararouter:gpt-5.6-luna"})
        self.assertEqual(judge.target()["model"], "agnes-2.5-flash")

    def test_configured_fallback_routes_to_its_provider_after_404(self):
        os.environ["MIRSAL_LLM_MODEL"] = "mimo-v2.6-flash"
        os.environ["MIRSAL_LLM_FALLBACK"] = "openai:gpt-5.6-luna"
        failure = llm.LLMError("model unavailable", kind="http", code=404)
        answer = {"choices": [{"message": {"content": "fallback"}, "finish_reason": "stop"}]}
        with mock.patch.object(llm, "_post", side_effect=[failure, answer]) as post:
            self.assertEqual(llm._complete_on("openai", "s", "u")[0], "fallback")
            self.assertEqual(post.call_count, 2)
            self.assertTrue(post.call_args_list[-1].args[0].startswith("https://api.openai.com/"))

    def test_vision_403_retries_the_pinned_openai_or_local_choice_on_nararouter(self):
        os.environ["MIRSAL_LLM_FALLBACK"] = "agnes-2.5-flash"
        denied = llm.LLMError("Your plan does not include the requested model.", kind="http", code=403)
        answer = {"choices": [{"message": {"content": "a wave"}, "finish_reason": "stop"}]}
        for selected in ("openai:gpt-5.6-luna", "nararouter:gpt-5.6-luna", "local:qwen:2"):
            with self.subTest(selected=selected):
                llm.FORCE.set({"model": selected})
                with mock.patch.object(llm, "_post", side_effect=[denied, answer]) as post:
                    text, meta = llm.complete_vision("s", "u", images=[b"still"],
                        provider_="local" if selected.startswith("local:") else "openai", model_=selected,
                        base_url="http://local.example/v1" if selected.startswith("local:") else None)
                self.assertEqual(text, "a wave")
                self.assertEqual(post.call_count, 2)
                args = post.call_args_list[-1].args
                self.assertEqual((args[0], args[1]["model"], args[2]),
                                 ("https://router.example/v1/chat/completions", "agnes-2.5-flash", "router-key"))
                self.assertEqual(meta["fallback_from"], catalog.normalize_model(selected))
                self.assertEqual(meta["model_provider"], "nararouter")
                self.assertEqual(llm.FORCE.get()["model"], selected, "stored selections stay intact")

    def test_vision_stream_recovers_before_output_but_never_restarts_partial_output(self):
        os.environ["MIRSAL_LLM_FALLBACK"] = "agnes-2.5-flash"
        for partial in (False, True):
            with self.subTest(partial=partial):
                chunks, sent = [], []
                def stream(url, body, key, timeout, receive):
                    sent.append(body["model"])
                    if len(sent) == 1:
                        if partial:
                            receive("He is ")
                        raise llm.LLMError("refused", kind="http", code=403)
                    receive("He is waving.")
                    return {"choices": [{"message": {"content": "He is waving."}, "finish_reason": "stop"}]}
                with mock.patch.object(llm, "_post_stream", side_effect=stream):
                    if partial:
                        with self.assertRaisesRegex(llm.LLMError, "refused"):
                            llm.complete_vision("s", "u", provider_="openai", model_="openai:gpt-5.6-luna",
                                                images=[b"still"], on_delta=chunks.append)
                        self.assertEqual(sent, ["gpt-5.6-luna"])
                        self.assertEqual(chunks, ["He is "])
                    else:
                        text, _ = llm.complete_vision("s", "u", provider_="openai", model_="openai:gpt-5.6-luna",
                                                     images=[b"still"], on_delta=chunks.append)
                        self.assertEqual(sent, ["gpt-5.6-luna", "agnes-2.5-flash"])
                        self.assertEqual("".join(chunks), text)

    def test_vision_fallback_is_bounded_disabled_when_none_and_keeps_both_errors(self):
        os.environ["MIRSAL_LLM_FALLBACK"] = "agnes-2.5-flash"
        for selected, mode, calls in (("nararouter:agnes-2.5-flash", "openai", 1),
                                      ("openai:gpt-5.6-luna", "none", 0),
                                      ("openai:gpt-5.6-luna", "openai", 2)):
            with self.subTest(selected=selected, mode=mode):
                denied = llm.LLMError("subscription denied", kind="http", code=403)
                failed = llm.LLMError("router unavailable", kind="unreachable")
                with mock.patch.object(llm, "_post", side_effect=[denied, failed]) as post:
                    with self.assertRaises(llm.LLMError) as caught:
                        llm.complete_vision("s", "u", provider_=mode, model_=selected, images=[b"still"])
                self.assertEqual(post.call_count, calls)
                if calls == 2:
                    self.assertIn("subscription denied", str(caught.exception))
                    self.assertIn("router unavailable", str(caught.exception))

    def test_vision_does_not_retry_without_a_configured_fallback_or_on_success(self):
        answer = {"choices": [{"message": {"content": "a wave"}, "finish_reason": "stop"}]}
        with mock.patch.object(llm, "_post", return_value=answer) as post:
            llm.complete_vision("s", "u", provider_="openai", model_="openai:gpt-5.6-luna", images=[b"still"])
            self.assertEqual(post.call_count, 1)
        with mock.patch.object(llm, "_post", side_effect=llm.LLMError("no access")) as post:
            with self.assertRaisesRegex(llm.LLMError, "no access"):
                llm.complete_vision("s", "u", provider_="openai", model_="openai:gpt-5.6-luna", images=[b"still"])
            self.assertEqual(post.call_count, 1)

    def test_description_and_judge_use_fallback_and_record_the_actual_model(self):
        from pathlib import Path
        from PIL import Image
        from mirsal.vision import describe
        from mirsal.runtime import cache
        from tests.test_vision import GOOD
        os.environ["MIRSAL_LLM_FALLBACK"] = "agnes-2.5-flash"
        os.environ["MIRSAL_DB_WRITE"] = "0"
        llm.FORCE.set({"model": "openai:gpt-5.6-luna"})
        out = Path(self.td.name)
        gen = out / "G001"
        gen.mkdir()
        image = io.BytesIO()
        Image.new("RGBA", (64, 64), (200, 20, 20, 255)).save(image, "PNG")
        (gen / "s9.png").write_bytes(image.getvalue())
        (gen / "result.json").write_text(json.dumps({"generation_id": "G001", "stickers": [{"index": 9, "key": "wave", "status": "READY", "png": "s9.png"}]}))
        denied = llm.LLMError("plan does not include this model", kind="http", code=403)
        answer = {"choices": [{"message": {"content": "He is waving."}, "finish_reason": "stop"}]}
        with mock.patch.object(llm, "_post_stream", side_effect=[denied, answer]):
            self.assertEqual(describe.sticker(out, "G001", 9, "what is he doing?", allowed=True), "He is waving.")
        answer["choices"][0]["message"]["content"] = GOOD
        with mock.patch.object(llm, "_post", side_effect=[denied, answer]):
            result = judge.VisionJudge(out=out, cache=cache.Cache(force_memory=True)).judge_sticker(
                image.getvalue(), {"name": "wave"}, generation_id="G001", sticker_id="G001/S9")
            self.assertEqual((result.decision, result.model), ("APPROVE", "agnes-2.5-flash"))
        logged = [json.loads(row) for row in (out / "model_calls.jsonl").read_text().splitlines()]
        self.assertEqual([row["kind"] for row in logged], ["VLM_DESCRIBE", "VLM_STICKER"])
        for row in logged:
            self.assertEqual(row["model"], "agnes-2.5-flash")
            self.assertEqual(row["fallback_from"], "openai:gpt-5.6-luna")
