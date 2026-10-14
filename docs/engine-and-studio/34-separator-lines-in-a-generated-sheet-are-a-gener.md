# Separator lines in a generated sheet are a generator artefact, not a cut bug (known cause, 2026-10-03)

<sub>Part of [engine-and-studio.md](../engine-and-studio.md).</sub>

The "Batman Lego pieces" sheet (G100) came back from the image model with random separator lines drawn through it (white divider crosses). The cut did nothing wrong: a sticker batch cuts by the layout it detects and blocks a cell whose subject crosses a cell border
(`inside_cell`, an overridable judgement call), which is the right verdict for a line that really crosses a cell. **The cut is not weakened** and the test that pins it stays (`tests/test_particle_set.py::test_the_white_divider_cross_of_the_real_g100_no_longer_kills_cells`:
a sticker batch still blocks, a particle batch cuts exact equal cells with a 2% inset that wipes the divider). The ways out are: cut it again as particles (`POST /api/generations/{id}/recut_particles`, free), allow the cell (`Use it anyway`), or open the slice
in the editor, erase the lines and save: the batch's sheet is rebuilt with that slice fixed and keeps its S#.

Separator cleanup remains an explicit recut-as-particles or editor operation. There is no automatic grey/white-line interpolation pass: colour alone cannot distinguish a divider from light artwork, and replacing whole rows would destroy valid cells.

The particle entry carries the batch or library sticker scope. Approve as a pack offers the existing modal scoped to the batch and returns to particles when adding succeeds. It spends nothing.
