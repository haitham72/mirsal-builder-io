import os
os.environ["MIRSAL_NO_REAL_CLI"] = "1"       # no test may reach the real Higgsfield CLI (it spends credits)
# no test may reach a language model either: not OpenAI (it bills), not the local LM Studio (slow, different on every machine). A test that needs an answer
# passes a fake (`Brain(complete=...)`, `mock.patch.object(llm, "complete", ...)`) or sets a provider for itself and puts it back.
os.environ["MIRSAL_LLM_PROVIDER"] = "none"
os.environ["MIRSAL_AGENT_PROVIDER"] = "none"
os.environ["MIRSAL_VISION_PROVIDER"] = "none"
