# Files and names

<sub>Part of [generation.md](../generation.md).</sub>

The engine keeps its files in `out/G00N/` and `out/jobs/` under its own names (`{media}-{subject}-{action}-{UTC time}-{hash}.{ext}`, `runtime/names.py`; older batches keep `<media>-<NNN>-<task_slug>-<key>`; the database stores them and they never change once made). `POST /api/generations/<id>/reveal` opens the batch's folder in the file manager (the Studio's **Open folder**), `GET .../files` returns the paths. The watch folders
(`inputs/Images_gen`, `videos_gen`) are never written to: a returned Kling video is laid out for the normalised video sheet, so pairing it with the raw sheet there would be wrong (and a
prepared pair dropped there is picked up as before).
