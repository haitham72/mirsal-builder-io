# Other commands (Windows / macOS / Linux)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

```
python -m mirsal create "create teddy yellow bear for school"    # same pipeline from the CLI
python -m mirsal more | animate [G001] [--slice N]
python -m mirsal test fast                            # stdlib unittest underneath: no pytest needed (docs/testing.md; slow tier and full discovery are retired: never run or requested)
```

Python >= 3.10. Everything uses `pathlib`; paths come from `mirsal/runtime/paths.py` (`MIRSAL_INPUT`, `MIRSAL_OUT` override; `MIRSAL_FFMPEG` overrides ffmpeg).
