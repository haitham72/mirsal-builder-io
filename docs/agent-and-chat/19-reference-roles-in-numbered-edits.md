# Reference roles in numbered edits

<sub>Part of [agent-and-chat.md](../agent-and-chat.md).</sub>

`resolver.resolve` already records reference roles. Numbered edits now attach references whose target is the edited sticker or unspecified, and `reference_roles_clause` binds each attached image's order to its requested style, pose, expression, colour, composition, subject or motion. For example, "make 5 with the style from S2 and pose from number 7" edits S5 alone and sends two references with separate style and pose instructions. Reference-source numbers are excluded from ordinary target-number resolution. A single STYLE reference retains the existing "make 5 like 2" clause. This covers explicit supported role syntax; general natural-language role inference and visual success remain unmeasured.
