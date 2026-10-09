import os
os.environ["MIRSAL_NO_REAL_CLI"] = "1"       # no test may reach the real Higgsfield CLI (it spends credits)
os.environ["MIRSAL_ADMIN_BOT"] = "0"
os.environ["MIRSAL_ACTIVITY"] = "0"            # the server's activity lines (runtime/activity.py) stay out of the test output           # the Telegram admin bot never runs in a test (services/admin_bot.py)
# no test may reach a language model either: not OpenAI (it bills), not the local LM Studio (slow, different on every machine). A test that needs an answer
# passes a fake (`Brain(complete=...)`, `mock.patch.object(llm, "complete", ...)`) or sets a provider for itself and puts it back.
os.environ["MIRSAL_LLM_PROVIDER"] = "none"
os.environ["MIRSAL_AGENT_PROVIDER"] = "none"
os.environ["MIRSAL_VISION_PROVIDER"] = "none"
# the real mirsal/.env may say MIRSAL_DB_WRITE=1, which would send every test's idempotency keys, tasks and jobs to the developer's real Postgres (and make a key from one
# run answer the next): off for the suite; a test that needs the write-through turns it on for itself (tests/test_jobqueue.py).
os.environ["MIRSAL_DB_WRITE"] = "0"
# tracing is off for the suite whatever mirsal/.env says: a test must never post a run (a prompt, a decision) to the developer's LangSmith project; test_trace turns it on against a fake server.
os.environ["MIRSAL_TRACE"] = "none"
# langgraph / langchain read these on their own, whatever MIRSAL_TRACE says, and mirsal/.env is per-machine and git-ignored: pinned so a fresh box or CI never posts the suite's runs to LangSmith.
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
