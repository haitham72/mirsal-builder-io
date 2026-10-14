# The step trace

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

The small queue the chat shows while the agent works (`message.steps[]`, `{kind, label, detail, status}` with kind `task | step | note | final`):

```
┌ generating teddy bear
│
●  expand prompt  >          (opens the nine names)
│
●  added your preferences  >
│
◇  you consistently asked for a wider range of emotions     (what the memory contributed)
│
└  plan ready · about 2 credits
```

`Trace._add` saves the session after each appended step. A restart retains the steps already written; the work between saves cannot be reconstructed. While the agent works the last row reads "Thinking"; when it is done the trace collapses to one line ("5 steps · plan ready") that opens it again. The page polls the
session while anything still moves: only the **newest** assistant message holds the live plan card (the pending Create), and a read or paint that fails is retried
instead of ending the polling (a frame that throws must never freeze the chat on "Thinking").
