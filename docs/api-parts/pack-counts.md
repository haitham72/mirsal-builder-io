# Pack presentation counts

Library snapshots expose additive sticker_count and reaction_count per pack and at the filtered snapshot root. Public Trending summaries expose the same pair from media.library.pack_counts. A reaction is an item whose source.particle_set is populated; classification stays on the backend. Existing stickers arrays, total, public stickers count, URLs and visibility rules are unchanged. No item is removed. Counts are calculated after existing ownership/public visibility filtering. Older responses without fields remain supported by presenters.
