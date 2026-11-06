# WeatherGPT — Project Overview

A ChatGPT/Gemini-style chat UI in front of a weather agent, with a
collapsible, drag-resizable right panel that shows tool-generated charts and
a live Leaflet map of geojson overlays — all pushed over Socket.IO
independently of the chat turn itself.

## 1. High-level architecture

```
Browser (templates/index.html + static/js/main.js)
   │
   │ HTTP (session cookie)             Socket.IO (per-user room)
   │                                          ▲
   ▼                                          │
Flask app (app.py)  ───────────────────────────
   │            ▲
   │ imports    │ posts to
   ▼            │
agent_module.py │
 (your agent,   │
  text only)    │
                │
        Your tools (image generator, geojson producer)
        call /get_tool_images and /get_tool_geojson directly,
        server-to-server, whenever they finish rendering something —
        NOT as part of the chat request/response cycle.
```

Two independent data paths reach the browser:

1. **The chat path** — synchronous, request/response. The browser calls
   `/api/chat`, Flask calls `agent_module.handle_message(...)`, and the
   markdown reply comes straight back in that same HTTP response.
2. **The tool path** — asynchronous, fire-and-forget from the tool's point
   of view. Whenever your image-generation tool or your geojson-producing
   tool finishes its work (which may take longer than the chat reply, or
   may not even be triggered by the current message), it POSTs the result
   to Flask, which relays it to the right browser over Socket.IO. The
   browser doesn't poll for this — it just listens.

Because these two paths are decoupled, the chat reply always comes back
quickly even if a chart is still rendering, and a tool can push a new image
or map overlay at any time, not just right after a user message.

## 2. Request lifecycle, step by step

**A user sends a chat message:**
1. Browser: `main.js` posts `{ conversation_id, message }` to `POST
   /api/chat`, using the browser's session cookie.
2. Flask (`app.py`): reads `session['user_id']`, loads that user's
   conversation from `data/conversations/<user_id>.json`, appends the
   user's message.
3. Flask calls `agent_module.handle_message(user_input, history)`, which
   returns **markdown text only**.
4. Flask appends the assistant's markdown to the same conversation file and
   returns `{ conversation_id, title, markdown }` as the HTTP response.
5. Browser: renders the user's prompt as plain text (exactly as typed) and
   the assistant's markdown through `marked.js` → `DOMPurify.sanitize` →
   `innerHTML`.

**A tool produces an image, at any point:**
1. Your image-generation tool (wherever it runs) has: the target `user_id`
   (whoever's session this belongs to), optionally a `conversation_id`, and
   the rendered image bytes.
2. It does an HTTP POST to `/get_tool_images` — `multipart/form-data` with
   fields `user_id`, `conversation_id` (optional), and `image` (the file).
3. Flask reads the file, base64-encodes it, and does
   `socketio.emit("weather_image", {conversation_id, image_base64, mime},
   room=user_id)`. `room=user_id` is what keeps this private to one
   browser — every logged-in browser tab joins a Socket.IO room named after
   its own `user_id` on connect (`join_room(user_id)` in the `connect`
   handler), so this event only reaches sockets in that room.
4. Browser: already has a live Socket.IO connection (`const socket =
   io()`, opened once on page load). Its `socket.on("weather_image", ...)`
   handler fires, decodes the base64 into a `data:` URL, sets
   `#viz-image.src`, and opens the right panel (`setVizOpen(true)`) if it
   was collapsed.

**A tool produces a geojson overlay, at any point:**
1. Your geojson-producing tool POSTs JSON to `/get_tool_geojson`:
   `{ user_id, conversation_id?, geojson, data? }`. `geojson` is a
   Feature/FeatureCollection; `data` is whatever you want shown on hover
   (e.g. `{ temperature_c: 24, humidity: "60%" }`).
2. Flask relays it as-is: `socketio.emit("weather_geojson", {conversation_id,
   geojson, data}, room=user_id)`.
3. Browser: `socket.on("weather_geojson", ...)` fires, opens the panel,
   switches to the **Map** tab, lazily creates the Leaflet map on first use
   (`L.map("viz-map-root")` + an OpenStreetMap tile layer), then adds the
   incoming geojson as its own `L.geoJSON(...)` layer with a bound tooltip
   built from `data`. Point geometries render as small circle markers so a
   single weather-station coordinate is actually visible on the map.
   **Nothing is ever removed** — every call to this handler pushes a new
   layer onto an array (`geojsonLayers`) and grows the map's fitted bounds
   to include it, so several turns of overlays accumulate on one map.

Both tool routes ignore Flask's normal session/login system on purpose —
they're server-to-server calls with no browser cookie attached, which is
why the caller must supply `user_id` explicitly. An optional shared secret
(`INTERNAL_TOOL_TOKEN` env var + `X-Internal-Token` header) is available if
you want to lock these two routes down beyond network-level trust.

## 3. Frontend layout

Three-panel grid (`.app` in `style.css`), left to right:

| Column | Content | Width |
|---|---|---|
| Rail (dark) | New-conversation button, conversation list, projects placeholder, user/settings, logout | fixed 260px |
| Conversation (middle) | Message history + composer | flexible (`1fr`) |
| Resizer | Drag handle | 6px when the right panel is open, 0 when closed |
| Visualization (right) | Visualization/Map tabs, chart image or Leaflet map | 0 when closed, otherwise whatever width you've dragged it to (default 360px) |

The grid's column widths are driven entirely from JavaScript
(`applyLayout()` in `main.js`, which writes `el.app.style.gridTemplateColumns`
directly) rather than from CSS classes, so opening/closing the panel and
dragging the resizer both go through the same code path. Dragging the
divider (`#viz-resizer`, pointer events) adjusts a `vizWidth` variable
between a 260px minimum and a (window-width-aware) maximum and re-applies
the grid on every pointer move.

## 4. Where things live

```
app.py                   Flask app: sessions, conversation API, chat route,
                          the two tool-facing routes, Socket.IO wiring
agent_module.py           REPLACE ME — your real agent plugs in here;
                          returns markdown text only
requirements.txt
templates/
  login.html               demo auth — swap for your real login
  index.html               3-column layout + resizer + viz tabs
static/
  css/style.css            design tokens, grid, viz panel, map styling
  js/main.js                conversation state, markdown rendering,
                            resizer drag logic, Socket.IO handlers,
                            Leaflet map management
data/conversations/        one JSON file per user_id (runtime-created)
flask_session/              Flask-Session's file store (runtime-created)
```

## 5. Swap-in points for your real system

- **Auth** — `login()` in `app.py` is a placeholder that trusts any
  non-empty username. Replace its body with your real auth check; keep
  setting `session['logged_in'] = True` and `session['user_id'] = ...`.
- **Storage** — `load_conversations` / `save_conversations` in `app.py`
  read/write one JSON file per user. Swap these two functions for real
  database calls whenever you're ready; every route only talks to them.
- **Agent** — `agent_module.handle_message(user_input, history) -> str`.
  Replace the placeholder body with a call into your real agent.
- **Tools** — have your image and geojson tools POST to `/get_tool_images`
  and `/get_tool_geojson` respectively (shapes documented above and in
  `app.py`'s route docstrings) whenever they finish producing something,
  passing the `user_id` (and ideally `conversation_id`) of whoever asked
  for it.
