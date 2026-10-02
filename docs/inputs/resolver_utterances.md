# Chat resolver eval set (Haitham fills this in)

The deterministic resolver (`mirsal/mirsal/agent/resolver.py`) and the model behind it are measured on **40 labelled chat lines**: >= 95% must resolve to exactly the sticker ids you mean.
Write each line as a user would type it, with the batch it refers to and the exact ids you expect (`G012/S3`), including ambiguous ones where the right answer is a question.

Format, one line each (delete these examples when you add yours):

```
focus G012 | make number 3 less flattened | G012/S3
focus G012 | I like 2 and 7 but not 3 and 4 | +G012/S2 +G012/S7 -G012/S3 -G012/S4
focus G013, parent G012 | go back to the previous one | G012
focus G012 | which is the dog banana | ask: G012/S4 or G012/S5
```

Also add `transformation_examples.md` here later: requests like "dog as banana" with the concepts you expect.

Lines:

(none yet)
