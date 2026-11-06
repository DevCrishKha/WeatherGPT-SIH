// # Copyright (c) 2026 [Dev Crish Kha]. All rights reserved.
// #
// # This source code and all associated materials are proprietary and
// # confidential to [Dev Crish Kha]. Unauthorized copying, modification,
// # distribution, publication, sublicensing, or use of this code, in whole
// # or in part, is strictly prohibited without prior written permission
// # from the copyright holder.

(() => {
  "use strict";

  // ---------------------------------------------------------------------
  // Setup
  // ---------------------------------------------------------------------
  const userId = document.body.dataset.userId || "";
  marked.setOptions({ breaks: true, gfm: true });

  const el = {
    app: document.querySelector(".app"),
    convoList: document.getElementById("conversation-list"),
    messages: document.getElementById("messages"),
    emptyState: document.getElementById("empty-state"),
    convoTitle: document.getElementById("convo-title"),
    composer: document.getElementById("composer"),
    input: document.getElementById("composer-input"),
    sendBtn: document.getElementById("composer-send"),
    newChatBtn: document.getElementById("btn-new-chat"),
    userName: document.getElementById("user-name"),
    userAvatar: document.getElementById("user-avatar"),
    vizPanel: document.getElementById("viz-panel"),
    vizToggle: document.getElementById("btn-toggle-viz"),
    vizClose: document.getElementById("btn-close-viz"),
    vizImage: document.getElementById("viz-image"),
    vizEmpty: document.getElementById("viz-empty"),
    vizTabs: document.querySelectorAll(".viz-tab"),
    vizPanes: document.querySelectorAll(".viz-pane"),
    vizResizer: document.getElementById("viz-resizer"),
    clearOverlaysBtn: document.getElementById("btn-clear-overlays"),
  };

  let currentConversationId = null;
  let isSending = false;

  el.userName.textContent = userId || "You";
  el.userAvatar.textContent = (userId || "?").slice(0, 1);

  // ---------------------------------------------------------------------
  // Conversation list
  // ---------------------------------------------------------------------
  async function fetchConversations() {
    const res = await fetch("/api/conversations");
    if (!res.ok) return [];
    return res.json();
  }

  function renderConversationList(items) {
    el.convoList.innerHTML = "";
    if (items.length === 0) {
      const li = document.createElement("li");
      li.className = "rail-item rail-item--muted";
      li.textContent = "No conversations yet";
      el.convoList.appendChild(li);
      return;
    }
    for (const conv of items) {
      const li = document.createElement("li");
      li.className =
        "rail-item" + (conv.id === currentConversationId ? " is-active" : "");
      li.dataset.id = conv.id;

      const label = document.createElement("span");
      label.textContent = conv.title || "New conversation";
      label.style.overflow = "hidden";
      label.style.textOverflow = "ellipsis";

      const del = document.createElement("button");
      del.className = "delete-conv";
      del.title = "Delete conversation";
      del.innerHTML =
        '<svg viewBox="0 0 16 16" width="12" height="12"><path d="M3 4h10M6.5 4V2.5h3V4M4.5 4l.6 9h5.8l.6-9" stroke="currentColor" stroke-width="1.4" fill="none" stroke-linecap="round"/></svg>';
      del.addEventListener("click", async (e) => {
        e.stopPropagation();
        await fetch(`/api/conversations/${conv.id}`, { method: "DELETE" });
        if (conv.id === currentConversationId) startNewConversation(false);
        refreshConversationList();
      });

      li.appendChild(label);
      li.appendChild(del);
      li.addEventListener("click", () => openConversation(conv.id));
      el.convoList.appendChild(li);
    }
  }

  async function refreshConversationList() {
    renderConversationList(await fetchConversations());
  }

  // ---------------------------------------------------------------------
  // Message rendering
  // ---------------------------------------------------------------------
  function clearMessages() {
    el.messages.innerHTML = "";
  }

  function showEmptyState(show) {
    if (show) {
      el.messages.innerHTML = "";
      el.messages.appendChild(el.emptyState);
    }
  }

  function addUserMessage(text) {
    const wrap = document.createElement("div");
    wrap.className = "msg msg--user";
    const role = document.createElement("div");
    role.className = "msg-role";
    role.textContent = "You";
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    // The user's prompt is preserved exactly as typed -- plain text, never re-parsed.
    bubble.textContent = text;
    wrap.appendChild(role);
    wrap.appendChild(bubble);
    el.messages.appendChild(wrap);
    return wrap;
  }

  function addAssistantMessage(markdownText) {
    const wrap = document.createElement("div");
    wrap.className = "msg msg--assistant";
    const role = document.createElement("div");
    role.className = "msg-role";
    role.textContent = "WeatherGPT";
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble md";
    bubble.innerHTML = DOMPurify.sanitize(marked.parse(markdownText || ""));
    wrap.appendChild(role);
    wrap.appendChild(bubble);
    el.messages.appendChild(wrap);
    return wrap;
  }

  function addHtmlBlock(htmlContent) {
    const wrap = document.createElement("div");
    wrap.className = "msg msg--tool-html";
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble tool-html";
    bubble.innerHTML = DOMPurify.sanitize(htmlContent || "", {
      ADD_TAGS: ["style"],
    });
    wrap.appendChild(bubble);
    el.messages.appendChild(wrap);
    return wrap;
  }

  // Creates the temporary indicator bubble if it doesn't exist yet, and
  // swaps whatever's inside it (dots, or a tool's status text) -- there's
  // only ever one of these on screen, reused in place, never stacked.
  function setTypingIndicatorContent(node) {
    let wrap = document.getElementById("typing-indicator");
    if (!wrap) {
      wrap = document.createElement("div");
      wrap.className = "msg msg--assistant";
      wrap.id = "typing-indicator";
      const role = document.createElement("div");
      role.className = "msg-role";
      role.textContent = "WeatherGPT";
      const bubble = document.createElement("div");
      bubble.className = "msg-bubble";
      bubble.id = "typing-indicator-bubble";
      wrap.appendChild(role);
      wrap.appendChild(bubble);
      el.messages.appendChild(wrap);
    }
    document.getElementById("typing-indicator-bubble").replaceChildren(node);
    scrollToBottom();
    return wrap;
  }

  function addTypingIndicator() {
    const dots = document.createElement("div");
    dots.className = "typing";
    dots.innerHTML = "<span></span><span></span><span></span>";
    return setTypingIndicatorContent(dots);
  }

  // Swaps the temporary indicator's dots for a tool-supplied status line
  // (e.g. "Fetching weather data...") with a shimmering "wave" animation.
  // Reuses the same bubble -- each new status replaces the last, it never
  // stacks a new message per update.
  function showStatusMessage(text) {
    const span = document.createElement("span");
    span.className = "status-text";
    span.textContent = text;
    return setTypingIndicatorContent(span);
  }

  function removeTypingIndicator() {
    document.getElementById("typing-indicator")?.remove();
  }

  function scrollToBottom() {
    el.messages.scrollTop = el.messages.scrollHeight;
  }

  // ---------------------------------------------------------------------
  // Conversation loading / switching
  // ---------------------------------------------------------------------
  async function openConversation(id) {
    currentConversationId = id;
    const res = await fetch(`/api/conversations/${id}`);
    if (!res.ok) return;
    const conv = await res.json();

    el.convoTitle.textContent = conv.title || "New conversation";
    clearMessages();

    // Group any saved html_blocks by the message index they were attached
    // after, so each one replays in the same spot it appeared in live.
    const htmlBlocks = conv.html_blocks || [];
    const blocksByIndex = {};
    for (const b of htmlBlocks) {
      const idx = b.after_message_index;
      (blocksByIndex[idx] ||= []).push(b);
    }

    if (conv.messages.length === 0 && htmlBlocks.length === 0) {
      showEmptyState(true);
    } else {
      // blocks attached before any message existed yet (after_message_index -1)
      (blocksByIndex[-1] || []).forEach((b) => addHtmlBlock(b.html));
      conv.messages.forEach((m, i) => {
        if (m.role === "user") addUserMessage(m.content);
        else addAssistantMessage(m.content);
        (blocksByIndex[i] || []).forEach((b) => addHtmlBlock(b.html));
      });
      scrollToBottom();
    }
    refreshConversationList();
  }

  function startNewConversation(refresh = true) {
    currentConversationId = null;
    el.convoTitle.textContent = "New conversation";
    showEmptyState(true);
    if (refresh) refreshConversationList();
    el.input.focus();
  }

  // ---------------------------------------------------------------------
  // Sending messages
  // ---------------------------------------------------------------------
  async function sendMessage(text) {
    if (isSending || !text.trim()) return;
    isSending = true;
    el.sendBtn.disabled = true;

    if (el.messages.contains(el.emptyState)) clearMessages();
    addUserMessage(text);
    scrollToBottom();
    addTypingIndicator();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: currentConversationId,
          message: text,
        }),
      });
      const data = await res.json();
      removeTypingIndicator();

      if (!res.ok) {
        addAssistantMessage(
          `**Something went wrong:** ${data.error || "please try again."}`,
        );
      } else {
        currentConversationId = data.conversation_id;
        el.convoTitle.textContent = data.title || "New conversation";
        addAssistantMessage(data.markdown);
        refreshConversationList();
      }
      scrollToBottom();
    } catch (err) {
      removeTypingIndicator();
      addAssistantMessage(
        "**Connection error.** Check that the Flask server is running.",
      );
      scrollToBottom();
    } finally {
      isSending = false;
      el.sendBtn.disabled = false;
    }
  }

  el.composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = el.input.value;
    el.input.value = "";
    autoresize();
    sendMessage(text);
  });

  el.input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      el.composer.requestSubmit();
    }
  });

  function autoresize() {
    el.input.style.height = "auto";
    el.input.style.height = Math.min(el.input.scrollHeight, 200) + "px";
  }
  el.input.addEventListener("input", autoresize);

  el.newChatBtn.addEventListener("click", () => startNewConversation());

  // ---------------------------------------------------------------------
  // Right section: visualization panel
  // ---------------------------------------------------------------------
  function setVizOpen(open) {
    el.app.classList.toggle("viz-open", open);
    el.vizToggle.setAttribute("aria-pressed", String(open));
  }

  el.vizToggle.addEventListener("click", () => {
    setVizOpen(!el.app.classList.contains("viz-open"));
  });
  el.vizClose.addEventListener("click", () => setVizOpen(false));

  el.clearOverlaysBtn.addEventListener("click", clearGeojsonLayers);

  el.vizTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      el.vizTabs.forEach((t) => t.classList.toggle("is-active", t === tab));
      el.vizPanes.forEach((p) =>
        p.classList.toggle("is-active", p.dataset.pane === tab.dataset.tab),
      );
      if (tab.dataset.tab === "map") {
        initMap();
        // The pane was just made visible -- Leaflet needs a resize nudge
        // once the layout has settled, or it renders at the wrong size.
        setTimeout(() => map && map.invalidateSize(), 50);
      }
    });
  });

  // ---------------------------------------------------------------------
  // Leaflet map -- additive geojson overlays (nothing is ever cleared;
  // each event from the backend adds one more layer on top of the rest)
  // ---------------------------------------------------------------------
  let map = null;
  const geojsonLayers = [];

  function initMap() {
    if (map) return;
    map = L.map("viz-map-root", { worldCopyJump: true }).setView([20, 0], 2);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 19,
    }).addTo(map);
  }

  function formatHoverContent(geojsonData, dataDict) {
    const props = (geojsonData && geojsonData.properties) || {};
    const name = (props.name || props.title || "Location").replace(
      /\n/g,
      "<br>",
    );
    const rows = Object.entries(dataDict || {})
      .map(([k, v]) => `<div><strong>${k}:</strong> ${v}</div>`)
      .join("");
    return `<div class="map-hover"><div class="map-hover-title">${name}</div>${rows}</div>`;
  }

  const DEFAULT_GEOJSON_COLOR = "#2E6F6B";
  function addGeojsonLayer(geojson, dataDict, color) {
    initMap();
    const c = color || DEFAULT_GEOJSON_COLOR;

    const layer = L.geoJSON(geojson, {
      // polygons and lines (this is what was defaulting to blue)
      style: () => ({
        color: c, // outline
        weight: 2,
        fillColor: c,
        fillOpacity: 0.3,
      }),
      // points
      pointToLayer: (feature, latlng) =>
        L.circleMarker(latlng, {
          radius: 7,
          weight: 2,
          color: c,
          fillColor: c,
          fillOpacity: 0.55,
        }),
      onEachFeature: (feature, lyr) => {
        lyr.bindTooltip(formatHoverContent(feature, dataDict), {
          sticky: true,
        });
      },
    }).addTo(map);
    geojsonLayers.push(layer);

    try {
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        // Grow to include everything plotted so far, don't just snap to the newest.
        const combined = geojsonLayers.reduce(
          (acc, l) =>
            l.getBounds().isValid() ? acc.extend(l.getBounds()) : acc,
          L.latLngBounds(bounds),
        );
        map.fitBounds(combined, { maxZoom: 9, padding: [24, 24] });
      }
    } catch (e) {
      // some geometries (e.g. a single Point) still resolve to a valid bounds via circleMarker
    }
  }

  function clearGeojsonLayers() {
    // Remove every tracked overlay layer from the map...
    geojsonLayers.forEach((layer) => {
      if (map) map.removeLayer(layer);
    });
    // ...then empty the array in place, so future fitBounds() calls
    // don't try to include layers that no longer exist.
    geojsonLayers.length = 0;
  }

  // ---------------------------------------------------------------------
  // Socket.IO -- receive tool-generated images and geojson overlays,
  // pushed from /get_tool_images and /get_tool_geojson (see app.py)
  // ---------------------------------------------------------------------
  const socket = io();

  socket.on("connect", () => {
    console.log("Socket connected:", socket.id);
  });

  socket.on("weather_image", (payload) => {
    console.log("weather_image RECEIVED:", payload);

    if (
      payload.conversation_id &&
      payload.conversation_id !== currentConversationId
    ) {
      console.log("Image rejected because conversation_id doesn't match");
      console.log("Received:", payload.conversation_id);
      console.log("Current:", currentConversationId);
      return;
    }

    console.log("Image base64 length:", payload.image_base64?.length);
    console.log("MIME:", payload.mime);

    el.vizImage.src = `data:${payload.mime || "image/png"};base64,${payload.image_base64}`;

    el.vizImage.hidden = false;
    el.vizEmpty.hidden = true;

    setVizOpen(true);
  });

  socket.on("weather_geojson", (payload) => {
    if (
      payload.conversation_id &&
      payload.conversation_id !== currentConversationId
    ) {
      console.log("conversation_id does not match");
      return;
    }

    setVizOpen(true);
    // switch to the Map tab so the new overlay is actually visible
    const mapTab = Array.from(el.vizTabs).find((t) => t.dataset.tab === "map");
    if (mapTab && !mapTab.classList.contains("is-active")) mapTab.click();
    addGeojsonLayer(payload.geojson, payload.data, payload.color); // <-- changed
    setTimeout(() => map && map.invalidateSize(), 50);
  });

  socket.on("weather_html", (payload) => {
    if (
      payload.conversation_id &&
      payload.conversation_id !== currentConversationId
    )
      return;
    addHtmlBlock(payload.html);
    scrollToBottom();
  });

  socket.on("tool_status", (payload) => {
    if (
      payload.conversation_id &&
      payload.conversation_id !== currentConversationId
    )
      return;
    // Ignore stray/late status pushes once the chat turn has already
    // finished (removeTypingIndicator already ran) -- otherwise a slow
    // tool could resurrect the indicator after the real answer is shown.
    if (!isSending) return;
    showStatusMessage(payload.message);
  });

  // ---------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------
  (async function init() {
    const items = await fetchConversations();
    renderConversationList(items);
    if (items.length > 0) {
      await openConversation(items[0].id);
    } else {
      startNewConversation(false);
    }
  })();
})();
