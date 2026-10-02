# Pool search eval set (Haitham fills this in)

`python -m mirsal pool search "<query>"` is measured against this file: **precision@5 >= 0.8** on the queries that have answers, and **nothing returned** for the queries that must return nothing.
Write about 30 queries in the form "{topic} doing {action}" in English, Arabic and Arabizi, each with the sticker ids you consider right (see them with `python -m mirsal list` / `show G002`),
plus at least 5 that should return nothing.

Format, one line per query (delete these examples when you add yours):

```
batman throwing | G002/S2
angel reading a newspaper | G001/S1 G001/S2 G001/S3
صقر يرقص | (nothing)
penguin skiing | (nothing)
```

Queries:

(none yet)
