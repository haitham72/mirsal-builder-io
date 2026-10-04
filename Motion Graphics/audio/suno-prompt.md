# Suno prompt: the reel's music (30 s, 128 BPM)

The reel (`app/src/scenes/reel.ts`) is cut to a 128 BPM grid of 64 beats: an intro of 8 beats (0 to 3.75 s), the
first drop at 3.75 s, a break at about 20.6 s, a second drop at 21.6 s, a build from 26.25 s, and the logo hit at
27.9 s. Until a Suno track exists, `analysis/reel_mix.py` synthesises a placeholder on the same grid.

In Suno: Custom mode, **Instrumental** on.

**Style**

```
128 BPM, instrumental, high-energy modern electronic pop product-launch ad, punchy four-on-the-floor kick, crisp claps, fast shimmering hi-hats, bright glossy synth plucks, sparkly arpeggios, deep clean sub bass, short riser into a hard drop, premium and playful like an Apple or Google launch film, very clean mix, no vocals
```

**Lyrics / structure box**

```
[Intro: filtered plucks and ticking hi-hats, riser building, 2 bars]
[Drop: full beat hits hard, bright plucks, 6 bars]
[Break: half-time for 1 bar, sparkly arpeggio]
[Drop 2: full energy, 4 bars, stutter edits]
[Outro: big final impact, short shimmering tail]
```

**Using the track.** Save it as `audio/suno.mp3`. Suno makes 1 to 2 minutes; the first drop is lined up to the
reel's 3.75 s drop, the result trimmed to 30 s, and the tempo stretched to exactly 128 BPM if it drifted. Then set
`MUSIC` in `analysis/reel_mix.py` to it and run the mix again: the sound effects stay where they are.
