# 1. Shared shell

<sub>Part of [design.md](../design.md).</sub>

Every screen uses the same rail, palette, typography and responsive layout. Desktop has a 96px rail and, on list-bearing routes, a 392px second column; at widths up to 1180px that column becomes 300px. Below 900px the list is a drawer; below 760px the rail becomes a bottom bar on every route. Home and Settings use the main column without a list. The four rail items are Home, Create, Library and Help; the avatar menu holds account and staff tools.

`app.js` owns navigation and event dispatch. Create has Chat / Studio tabs and a New menu. `studio.css` defines shared geometry and light tokens, `agent.css` supplies namespaced chat styles, and `theme.css` maps the dark theme. Queue controls reserve space below content while jobs are listed. Built screen details follow in §5; unresolved visual decisions remain in the trackers.
