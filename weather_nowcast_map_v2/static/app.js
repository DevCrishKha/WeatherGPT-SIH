const map = L.map("map").setView([22.5, 79.0], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let districtLayer = null;
let nowcastByDistrict = new Map();

const statusElement = document.getElementById("status");
const refreshButton = document.getElementById("refresh-button");

// Adjust these values if your IMD color code has a different meaning.
const COLOR_BY_CODE = {
  1: "#2e7d32",
  2: "#f9a825",
  3: "#ef6c00",
  4: "#c62828",
};

function normalizeDistrictName(name) {
  return String(name || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Za-z0-9]/g, "")
    .toUpperCase();
}

function getDistrictName(feature) {
  const properties = feature.properties || {};
  return String(
    properties.district ||
      properties.DISTRICT ||
      properties.District ||
      properties.dtname ||
      properties.NAME_2 ||
      properties.NAME_3 ||
      properties.name ||
      "",
  )
    .trim()
    .toUpperCase();
}

function styleDistrict(feature) {
  const districtName = getDistrictName(feature);
  const nowcast = nowcastByDistrict.get(normalizeDistrictName(districtName));

  return {
    color: "#555",
    weight: 0.7,
    fillColor: nowcast
      ? COLOR_BY_CODE[nowcast.color_code] || "#9e9e9e"
      : "#d6d6d6",
    fillOpacity: nowcast ? 0.75 : 0.25,
  };
}

function onEachDistrict(feature, layer) {
  const districtName = getDistrictName(feature);
  const nowcast = nowcastByDistrict.get(normalizeDistrictName(districtName));

  if (nowcast) {
    layer.bindTooltip(nowcast.warning_html, {
      sticky: true,
      direction: "top",
      opacity: 0.95,
    });

    layer.bindPopup(nowcast.warning_html);
  } else {
    layer.bindTooltip(
      `<strong>${districtName || "Unknown district"}</strong><br>No nowcast record available.`,
      { sticky: true },
    );
  }

  layer.on({
    mouseover: (event) => {
      event.target.setStyle({
        weight: 2,
        color: "#111",
      });
    },
    mouseout: (event) => {
      districtLayer.resetStyle(event.target);
    },
  });
}

async function loadMap() {
  statusElement.textContent = "Fetching nowcast data...";

  try {
    const [nowcastResponse, geojsonResponse] = await Promise.all([
      fetch("/api/nowcast"),
      fetch("/static/districts.geojson"),
    ]);

    const nowcastPayload = await nowcastResponse.json();

    if (!nowcastResponse.ok) {
      throw new Error(nowcastPayload.error || "Nowcast request failed.");
    }

    if (!geojsonResponse.ok) {
      throw new Error("Could not load district boundary file.");
    }

    const topology = await geojsonResponse.json();
    const objectName = Object.keys(topology.objects)[0];
    if (!objectName) {
      throw new Error("No map object found in the TopoJSON file.");
    }
    const geojson = topojson.feature(topology, topology.objects[objectName]);

    nowcastByDistrict = new Map(
      nowcastPayload.districts.map((item) => [
        normalizeDistrictName(item.district),
        item,
      ]),
    );

    console.table(
      nowcastPayload.districts.map((item) => ({
        imdDistrict: item.district,
        colorCode: item.color_code,
      })),
    );

    const district_table = JSON.stringify(
      nowcastPayload.districts.map((item) => ({
        imdDistrict: item.district,
        colorCode: item.color_code,
      })),
    );
    fetch(`/save/district_table`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: district_table,
    });

    if (districtLayer) {
      map.removeLayer(districtLayer);
    }

    districtLayer = L.geoJSON(geojson, {
      style: styleDistrict,
      onEachFeature: onEachDistrict,
    }).addTo(map);

    if (districtLayer.getBounds().isValid()) {
      map.fitBounds(districtLayer.getBounds());
    }

    const matchedCount = geojson.features.filter((feature) =>
      nowcastByDistrict.has(normalizeDistrictName(getDistrictName(feature))),
    ).length;

    statusElement.textContent =
      `Loaded ${nowcastPayload.districts.length} IMD records; ${matchedCount} matched map districts. ` +
      `Unmatched districts remain visible and show “No nowcast record available”.`;
  } catch (error) {
    console.error(error);
    statusElement.textContent = `Error: ${error.message}`;
  }
}

refreshButton.addEventListener("click", loadMap);
loadMap();
