"""The AI backend choice (services/llm.py): auto | local | cloud, the kept choice in auto mode, the Qwen think-block prefill and the shared JSON reader."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mirsal.services import llm


class Env:
    """A scratch out/ for the saved choice, the provider env set to auto, a fake key, and everything put back."""

    def __enter__(self):
        self.td = tempfile.TemporaryDirectory()
        self.keep = {k: os.environ.get(k) for k in ("MIRSAL_OUT", "MIRSAL_LLM_PROVIDER", "MIRSAL_AI_BACKEND", llm.KEY_VAR, "MIRSAL_LOCAL_PREFILL")}
        os.environ["MIRSAL_OUT"] = self.td.name
        os.environ["MIRSAL_LLM_PROVIDER"] = "auto"
        os.environ.pop("MIRSAL_AI_BACKEND", None)
        os.environ[llm.KEY_VAR] = "sk-test"
        llm._sticky.update(prov=None, until=0.0)
        return self

    def __exit__(self, *a):
        for k, v in self.keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        llm._sticky.update(prov=None, until=0.0)
        self.td.cleanup()


class BackendChoiceTests(unittest.TestCase):
    def test_default_is_auto_and_the_choice_is_saved_and_read_back(self):
        with Env():
            self.assertEqual(llm.preference(), "auto")
            self.assertEqual(llm.set_preference("cloud"), "cloud")
            self.assertEqual(llm.preference(), "cloud")
            with self.assertRaises(llm.LLMError):
                llm.set_preference("moon")

    def test_a_chosen_backend_is_used_even_when_the_other_is_up(self):
        with Env(), mock.patch.object(llm, "local_reachable", return_value=True):
            llm.set_preference("cloud")
            self.assertEqual(llm.provider(), "openai")
            llm.set_preference("local")
            self.assertEqual(llm.provider(), "local")

    def test_cloud_without_a_key_is_none_never_the_local_model(self):
        with Env(), mock.patch.object(llm, "local_reachable", return_value=True):
            os.environ.pop(llm.KEY_VAR)
            llm.set_preference("cloud")
            self.assertEqual(llm.provider(), "none")

    def test_auto_keeps_its_choice_instead_of_flipping_with_every_probe(self):
        with Env(), mock.patch.object(llm, "local_reachable", side_effect=[True, False, True]) as probe:
            self.assertEqual(llm.provider(), "local")
            # the probe now says "down" but the kept choice is local only while it is reachable; the first answer was cached for 10 minutes
            self.assertEqual(llm._sticky["prov"], "local")
            self.assertEqual(probe.call_count, 1)

    def test_a_failed_call_in_auto_moves_to_the_other_backend_and_retries_once(self):
        with Env(), mock.patch.object(llm, "local_reachable", return_value=True):
            seen = []

            def fake(prov, system, user, **kw):
                seen.append(prov)
                if prov == "local":
                    raise llm.LLMError("Cannot reach the AI service")
                return "ok", {"provider": prov}
            with mock.patch.object(llm, "_complete_on", side_effect=fake):
                self.assertEqual(llm.complete("s", "u")[0], "ok")
                self.assertEqual(seen, ["local", "openai"])
                seen.clear()
                llm.complete("s", "u")                                 # the kept choice is now the cloud: no new try on the local model
                self.assertEqual(seen, ["openai"])

    def test_a_chosen_backend_never_falls_back_to_the_other(self):
        with Env(), mock.patch.object(llm, "local_reachable", return_value=True):
            llm.set_preference("local")
            with mock.patch.object(llm, "_complete_on", side_effect=llm.LLMError("down")) as c:
                with self.assertRaises(llm.LLMError):
                    llm.complete("s", "u")
                self.assertEqual(c.call_count, 1)

    def test_availability_says_why(self):
        with Env(), mock.patch.object(llm, "local_reachable", return_value=False):
            os.environ.pop(llm.KEY_VAR)
            a = llm.availability()
            self.assertFalse(a["local"]["ok"])
            self.assertIn("LM Studio", a["local"]["why"])
            self.assertFalse(a["cloud"]["ok"])
            self.assertIn(llm.KEY_VAR, a["cloud"]["why"])

    def test_the_explicit_env_provider_still_wins(self):
        with Env():
            os.environ["MIRSAL_LLM_PROVIDER"] = "none"
            llm.set_preference("cloud")
            self.assertEqual(llm.provider(), "none")


class PrefillTests(unittest.TestCase):
    def _sent(self, model, prov="local"):
        sent = {}

        def post(url, body, key, timeout):
            sent.update(body)
            return {"choices": [{"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}], "usage": {}}
        with Env(), mock.patch.object(llm, "_post", post):
            llm._complete_on(prov, "sys", "user", model_=model)
        return sent["messages"]

    def test_a_qwen_model_gets_a_closed_think_block_as_the_last_message(self):
        msgs = self._sent("qwen3.5-4b:2")
        self.assertEqual(msgs[-1], {"role": "assistant", "content": llm.CLOSED_THINK})

    def test_other_models_and_the_cloud_get_none(self):
        self.assertEqual(self._sent("llama-3")[-1]["role"], "user")
        self.assertEqual(self._sent("gpt-4.1-mini", "openai")[-1]["role"], "user")

    def test_the_prefill_can_be_switched_off(self):
        with Env():
            os.environ["MIRSAL_LOCAL_PREFILL"] = "0"
            self.assertFalse(llm._prefill("qwen3.5-4b"))

    def test_an_empty_answer_that_ran_out_of_budget_is_an_error_not_an_empty_string(self):
        with Env(), mock.patch.object(llm, "_post", return_value={"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}):
            with self.assertRaises(llm.LLMError):
                llm._complete_on("local", "s", "u", model_="other")


class ExtractJsonTests(unittest.TestCase):
    def test_reads_through_think_blocks_fences_and_chatter(self):
        self.assertEqual(llm.extract_json('<think>{no}</think> Sure!\n```json\n{"a": [1, {"b": "}"}]}\n``` bye'), {"a": [1, {"b": "}"}]})

    def test_an_empty_or_jsonless_answer_raises_value_error(self):
        for t in ("", "   ", "no object here"):
            with self.assertRaises(ValueError):
                llm.extract_json(t)


if __name__ == "__main__":
    unittest.main()
