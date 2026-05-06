const BUNDLED_FIXTURES = [
  "inertial-3-rounds.json",
  "one-action-thrust.json",
  "gravity-7r-no-weapons.json",
  "gravity-7r-one-armed.json",
  "gravity-7r-both-armed.json",
  "gravity-7r-los-blocked.json",
  "gravity-4r-asteroid-collision.json",
  "gravity-4r-asteroid-velocity-collision.json",
  "firing-arc-both-away.json",
  "firing-arc-agent-a-forward.json",
  "firing-arc-both-forward.json",
  "firing-arc-pass-by-7r.json",
];

const SVG_NS = "http://www.w3.org/2000/svg";
const HEX_SIZE = 34;
const SQRT3 = Math.sqrt(3);
const DEFAULT_PLAY_INTERVAL_MS = 1050;
const SHIP_SCALE = 0.72;

const VISUAL_OBJECT_PROFILES = {
  asteroid: [
    [0, -18],
    [14, -10],
    [17, 5],
    [6, 18],
    [-13, 14],
    [-19, -3],
  ],
  ship: [
    [-18, -11],
    [6, -12],
    [21, -5],
    [28, 0],
    [21, 5],
    [6, 12],
    [-18, 11],
    [-26, 0],
    [-13, -15],
    [-3, -7],
    [-13, 15],
    [-3, 7],
  ],
};

let fixtures = [];
let selectedFixture = null;
let currentRoundIndex = 0;
let playTimer = null;
let loadedAudits = new Map();

const elements = {
  fixtureSelect: document.querySelector("#fixtureSelect"),
  fileInput: document.querySelector("#fileInput"),
  folderInput: document.querySelector("#folderInput"),
  reloadButton: document.querySelector("#reloadButton"),
  prevButton: document.querySelector("#prevButton"),
  playButton: document.querySelector("#playButton"),
  nextButton: document.querySelector("#nextButton"),
  roundSlider: document.querySelector("#roundSlider"),
  timeline: document.querySelector("#timeline"),
  resetButton: document.querySelector("#resetButton"),
  speedSelect: document.querySelector("#speedSelect"),
  roundLabel: document.querySelector("#roundLabel"),
  validationLabel: document.querySelector("#validationLabel"),
  hashLabel: document.querySelector("#hashLabel"),
  hashDetails: document.querySelector("#hashDetails"),
  copyHashButton: document.querySelector("#copyHashButton"),
  quorumLabel: document.querySelector("#quorumLabel"),
  phaseNote: document.querySelector("#phaseNote"),
  board: document.querySelector("#board"),
  agentCards: document.querySelector("#agentCards"),
  weaponList: document.querySelector("#weaponList"),
  diffList: document.querySelector("#diffList"),
  auditDetails: document.querySelector("#auditDetails"),
  rawState: document.querySelector("#rawState"),
};

init();

window.__rqpVisualRules = {
  verifyObjectsContainedInHex,
};

async function init() {
  wireControls();
  await loadBundledFixtures();
}

function wireControls() {
  elements.fixtureSelect.addEventListener("change", () => {
    const fixture = fixtures.find((item) => item.name === elements.fixtureSelect.value);
    selectFixture(fixture);
  });

  elements.fileInput.addEventListener("change", async (event) => {
    const loaded = await loadUploadedFixtures([...event.target.files]);
    if (loaded.length > 0) {
      fixtures = [...loaded, ...fixtures.filter((fixture) => fixture.source === "bundled")];
      renderFixtureOptions();
      selectFixture(loaded[0]);
    }
    elements.fileInput.value = "";
  });

  elements.folderInput.addEventListener("change", async (event) => {
    const loaded = await loadUploadedFixtures([...event.target.files]);
    if (loaded.length > 0) {
      fixtures = [...loaded, ...fixtures.filter((fixture) => fixture.source === "bundled")];
      renderFixtureOptions();
      selectFixture(loaded[0]);
    }
    elements.folderInput.value = "";
  });

  elements.reloadButton.addEventListener("click", loadBundledFixtures);
  elements.prevButton.addEventListener("click", () => setRound(currentRoundIndex - 1));
  elements.nextButton.addEventListener("click", () => setRound(currentRoundIndex + 1));
  elements.resetButton.addEventListener("click", () => setRound(0));
  elements.playButton.addEventListener("click", togglePlayback);
  elements.roundSlider.addEventListener("input", () => setRound(Number(elements.roundSlider.value)));
  elements.speedSelect.addEventListener("change", () => {
    if (playTimer) {
      stopPlayback();
      togglePlayback();
    }
  });
  elements.copyHashButton.addEventListener("click", copyCurrentHash);
  document.addEventListener("keydown", handleShortcut);
}

async function loadBundledFixtures() {
  stopPlayback();
  const loaded = [];
  const audits = await loadBundledAudits();
  for (const name of BUNDLED_FIXTURES) {
    try {
      const response = await fetch(`../fixtures/bootstrap/${name}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }
      loaded.push({
        name,
        source: "bundled",
        data: await response.json(),
        audit: audits.get(name) ?? null,
      });
    } catch (error) {
      console.warn(`Could not load ${name}:`, error);
    }
  }
  loadedAudits = new Map([...loadedAudits, ...audits]);
  fixtures = [...fixtures.filter((fixture) => fixture.source === "upload"), ...loaded];
  renderFixtureOptions();
  selectFixture(fixtures[0] ?? null);
}

async function loadBundledAudits() {
  const auditNames = new Set([
    ...BUNDLED_FIXTURES
      .filter((name) => name !== "inertial-3-rounds.json")
      .map((name) => name.replace(/\.json$/, "-audit.json")),
    "post-game-audit.json",
  ]);
  const audits = new Map();
  for (const name of auditNames) {
    try {
      const response = await fetch(`../fixtures/bootstrap/${name}`, { cache: "no-store" });
      if (!response.ok) continue;
      const audit = await response.json();
      if (name === "post-game-audit.json") {
        audits.set("inertial-3-rounds.json", audit);
      } else {
        audits.set(name.replace(/-audit\.json$/, ".json"), audit);
      }
    } catch (error) {
      console.warn(`Could not load audit ${name}:`, error);
    }
  }
  return audits;
}

async function loadUploadedFixtures(files) {
  const loaded = [];
  const audits = new Map();
  const replayFiles = [];

  for (const file of files) {
    if (!file.name.endsWith(".json") || file.name === "rfc5-fixture-index.json") {
      continue;
    }
    const displayName = file.webkitRelativePath || file.name;
    try {
      const data = JSON.parse(await file.text());
      if (data?.genesis?.world_state && Array.isArray(data.rounds)) {
        replayFiles.push({ file, displayName, data });
      } else if (file.name.endsWith("-audit.json") || file.name === "post-game-audit.json") {
        audits.set(file.name === "post-game-audit.json" ? "inertial-3-rounds.json" : file.name.replace(/-audit\.json$/, ".json"), data);
      }
    } catch (error) {
      console.warn(`Skipping ${file.name}:`, error);
    }
  }

  for (const replay of replayFiles) {
    loaded.push({
      name: `upload:${replay.displayName}`,
      source: "upload",
      data: replay.data,
      audit: audits.get(replay.file.name) ?? null,
    });
  }

  return loaded;
}

function renderFixtureOptions() {
  elements.fixtureSelect.replaceChildren(
    ...fixtures.map((fixture) => {
      const option = document.createElement("option");
      option.value = fixture.name;
      option.textContent = fixture.name;
      return option;
    }),
  );
}

function selectFixture(fixture) {
  stopPlayback();
  selectedFixture = fixture;
  currentRoundIndex = 0;

  if (!fixture) {
    elements.roundSlider.max = "0";
    renderEmptyState("No fixture loaded.");
    return;
  }

  elements.fixtureSelect.value = fixture.name;
  elements.roundSlider.max = String(fixture.data.rounds.length);
  elements.roundSlider.value = "0";
  renderTimeline();
  render();
}

function setRound(nextIndex) {
  if (!selectedFixture) {
    return;
  }
  const max = selectedFixture.data.rounds.length;
  currentRoundIndex = Math.max(0, Math.min(max, nextIndex));
  elements.roundSlider.value = String(currentRoundIndex);
  renderTimeline();
  render();

  if (playTimer && currentRoundIndex === max) {
    stopPlayback();
  }
}

function togglePlayback() {
  if (playTimer) {
    stopPlayback();
    return;
  }
  if (!selectedFixture) {
    return;
  }
  if (currentRoundIndex >= selectedFixture.data.rounds.length) {
    setRound(0);
  }
  elements.playButton.textContent = "Pause";
  playTimer = window.setInterval(() => {
    setRound(currentRoundIndex + 1);
  }, playbackDelay());
}

function stopPlayback() {
  if (playTimer) {
    window.clearInterval(playTimer);
    playTimer = null;
  }
  elements.playButton.textContent = "Play";
}

async function render() {
  if (!selectedFixture) {
    renderEmptyState("No fixture loaded.");
    return;
  }

  const fixture = selectedFixture.data;
  const state = currentWorldState(fixture, currentRoundIndex);
  const currentRound = currentRoundIndex === 0 ? null : fixture.rounds[currentRoundIndex - 1];
  const validation = await validateCurrentState(fixture, currentRoundIndex, state);
  const previousState = currentRoundIndex === 0 ? null : currentWorldState(fixture, currentRoundIndex - 1);
  const weaponEvents = currentRound ? buildWeaponEvents(fixture, currentRound, state) : [];
  const collisionEvents = buildCollisionEvents(previousState, state);

  elements.roundLabel.textContent = `${currentRoundIndex} / ${fixture.rounds.length}`;
  elements.validationLabel.textContent = validation.ok ? "Hash OK" : "Hash mismatch";
  elements.validationLabel.className = validation.ok ? "ok" : "bad";
  elements.hashLabel.textContent = shortHash(validation.actual);
  elements.hashLabel.dataset.fullHash = validation.actual;
  elements.hashDetails.textContent = validation.ok
    ? `expected = actual = ${validation.actual}`
    : `expected ${validation.expected} but got ${validation.actual}`;
  elements.quorumLabel.textContent = currentRound ? quorumText(currentRound) : "Genesis";
  elements.phaseNote.textContent = currentRound?.phase_note || fixture.description || "Genesis state";

  renderBoard(fixture, state, weaponEvents, collisionEvents);
  renderAgentCards(fixture, state);
  renderWeaponList(weaponEvents);
  renderDiffList(previousState, state);
  renderAuditDetails(selectedFixture.audit);
  elements.rawState.textContent = JSON.stringify(state, null, 2);
}

function renderEmptyState(message) {
  elements.board.replaceChildren();
  elements.agentCards.replaceChildren();
  elements.weaponList.replaceChildren();
  elements.diffList.replaceChildren();
  elements.roundLabel.textContent = "0 / 0";
  elements.validationLabel.textContent = "Not loaded";
  elements.hashLabel.textContent = "-";
  elements.quorumLabel.textContent = "-";
  elements.phaseNote.textContent = message;
}

function currentWorldState(fixture, roundIndex) {
  return roundIndex === 0 ? fixture.genesis.world_state : fixture.rounds[roundIndex - 1].world_state;
}

async function validateCurrentState(fixture, roundIndex, state) {
  const expected = roundIndex === 0 ? fixture.genesis.world_state_hash : fixture.rounds[roundIndex - 1].world_state_hash;
  const actual = await sha256Hex(canonicalStringify(state));
  return {
    ok: actual === expected,
    actual,
    expected,
  };
}

function renderBoard(fixture, state, weaponEvents, collisionEvents = []) {
  const bounds = boardBounds(fixture, state);
  const layout = createBoardLayout(bounds);
  const svg = elements.board;
  svg.replaceChildren();
  svg.setAttribute("viewBox", `${layout.minX - 70} ${layout.minY - 70} ${layout.width + 140} ${layout.height + 140}`);

  const defs = svgEl("defs");
  defs.appendChild(marker("arrow-railgun", "#ffd166"));
  defs.appendChild(marker("arrow-mazer", "#c084fc"));
  defs.appendChild(marker("arrow-laser", "#6ee7ff"));
  defs.appendChild(marker("arrow-blocked", "#ff5468"));
  defs.appendChild(marker("arrow-miss", "#7c8ba0"));
  svg.appendChild(defs);

  const gridLayer = svgEl("g", { class: "grid-layer" });
  for (let r = bounds.rMin; r <= bounds.rMax; r += 1) {
    for (let q = bounds.qMin; q <= bounds.qMax; q += 1) {
      const point = axialToPixel({ q, r });
      gridLayer.appendChild(svgEl("polygon", {
        class: "hex",
        points: hexPoints(point.x, point.y),
      }));
      gridLayer.appendChild(svgText(`${q},${r}`, point.x, point.y + 1.8, "hex-label"));
    }
  }
  svg.appendChild(gridLayer);

  const objectLayer = svgEl("g", { class: "object-layer" });
  for (const object of mapObjects(fixture, state)) {
    const point = axialToPixel(object.position);
    const classes = ["object"];
    if (object.opaque) classes.push("opaque");
    if (object.collides) classes.push("collides");
    objectLayer.appendChild(svgEl("polygon", {
      class: classes.join(" "),
      "data-visual-object": "map-object",
      "data-profile": "asteroid",
      "data-object-id": object.id || object.type || "object",
      "data-angle": "0",
      "data-scale": "1",
      points: asteroidPoints(point.x, point.y),
    }));
    objectLayer.appendChild(svgText(object.id || object.type || "object", point.x, point.y + 23, "ship-label"));
  }
  svg.appendChild(objectLayer);

  const rangeLayer = svgEl("g", { class: "range-layer" });
  for (const agent of state.agents) {
    if (agent.weapons?.includes("micro-micro-mazer")) {
      const point = axialToPixel(agent.position);
      rangeLayer.appendChild(svgEl("circle", {
        class: "range-ring",
        cx: point.x,
        cy: point.y,
        r: axialRangeRadius(fixture, "micro-micro-mazer"),
      }));
    }
  }
  svg.appendChild(rangeLayer);

  const annotationLayer = svgEl("g", { class: "annotation-layer" });
  for (const event of collisionEvents) {
    const point = axialToPixel(event.agent.position);
    annotationLayer.appendChild(svgEl("circle", {
      class: "impact-ring",
      cx: point.x,
      cy: point.y,
      r: "26",
    }));
    annotationLayer.appendChild(svgText("IMPACT", point.x, point.y - 30, "impact-label"));
  }
  svg.appendChild(annotationLayer);

  const weaponLayer = svgEl("g", { class: "weapon-layer" });
  for (const event of weaponEvents) {
    const from = axialToPixel(event.attacker.position);
    const to = axialToPixel(event.target.position);
    weaponLayer.appendChild(svgEl("line", {
      class: `weapon-line ${event.weaponId} ${event.kind}`,
      x1: from.x,
      y1: from.y,
      x2: to.x,
      y2: to.y,
      "marker-end": `url(#${event.hit ? markerId(event.weaponId) : event.kind === "blocked" ? "arrow-blocked" : "arrow-miss"})`,
    }));
  }
  svg.appendChild(weaponLayer);

  const shipLayer = svgEl("g", { class: "ship-layer" });
  for (const agent of state.agents) {
    shipLayer.appendChild(shipSprite(agent));
  }
  svg.appendChild(shipLayer);
}

function renderAgentCards(fixture, state) {
  const maxHp = Math.max(1, ...fixture.genesis.world_state.agents.map((agent) => agent.hp ?? 1));
  elements.agentCards.replaceChildren(
    ...state.agents.map((agent) => {
      const card = document.createElement("article");
      card.className = "agent-card";
      const hpPct = Math.max(0, Math.min(100, ((agent.hp ?? 0) / maxHp) * 100));
      const fuel = fuelForAgent(agent);
      card.innerHTML = `
        <h3>${escapeHtml(agent.agent_id)}</h3>
        <p>Position q=${agent.position.q}, r=${agent.position.r}</p>
        <p>Velocity dq=${agent.velocity?.dq ?? 0}, dr=${agent.velocity?.dr ?? 0}</p>
        <p>Facing dq=${agent.facing?.dq ?? 0}, dr=${agent.facing?.dr ?? 0}</p>
        <div class="hpbar" aria-label="HP"><span style="width:${hpPct}%"></span></div>
        <p>HP ${agent.hp}${agent.eliminated ? " - eliminated" : ""}</p>
        <div class="fuelbar" aria-label="Fuel"><span style="width:${Math.max(0, Math.min(100, fuel / 10))}%"></span></div>
        <p>Fuel ${fuel}</p>
      `;
      return card;
    }),
  );
}

function renderWeaponList(weaponEvents) {
  if (weaponEvents.length === 0) {
    elements.weaponList.replaceChildren(emptyCard("No weapon declarations this round."));
    return;
  }

  elements.weaponList.replaceChildren(
    ...weaponEvents.map((event) => {
      const card = document.createElement("article");
      card.className = "weapon-card";
      card.innerHTML = `
        <h3>${escapeHtml(event.attacker.agent_id)} -> ${escapeHtml(event.target.agent_id)}</h3>
        <p>${escapeHtml(event.weaponId)}: <strong class="${event.hit ? "ok" : "bad"}">${escapeHtml(event.label)}</strong></p>
        <p>${escapeHtml(event.reason)}</p>
      `;
      return card;
    }),
  );
}

function emptyCard(message) {
  const card = document.createElement("article");
  card.className = "weapon-card";
  card.textContent = message;
  return card;
}

function buildWeaponEvents(fixture, round, state) {
  const agents = new Map(state.agents.map((agent) => [agent.agent_id, agent]));
  const opaqueObjects = mapObjects(fixture, state).filter((object) => object.opaque);
  const events = [];

  for (const input of round.agent_inputs ?? []) {
    const attacker = agents.get(input.agent_id);
    if (!attacker) continue;
    for (const declaration of input.commit_payload?.weapons ?? []) {
      const target = agents.get(declaration.target_agent_id);
      if (!target) continue;
      const rule = weaponRule(fixture, declaration.weapon_id);
      const result = weaponResult(attacker, target, rule, opaqueObjects);
      events.push({
        attacker,
        target,
        weaponId: declaration.weapon_id,
        hit: result.hit,
        kind: result.kind,
        label: result.label,
        reason: result.reason,
      });
    }
  }

  return events;
}

function weaponResult(attacker, target, rule, opaqueObjects) {
  const distance = axialDistance(attacker.position, target.position);
  if (distance > rule.range) {
    return { hit: false, kind: "out-of-range", label: "out of range", reason: `out of range (${distance} > ${rule.range})` };
  }
  if (!isAxialStraight(attacker.position, target.position)) {
    return { hit: false, kind: "non-straight", label: "non-straight miss", reason: "not on a straight axial line" };
  }
  if (rule.arc === "forward" && !targetInForwardArc(attacker, target, distance)) {
    return { hit: false, kind: "out-of-arc", label: "out of arc", reason: "outside fixed forward arc" };
  }
  if (lineOfSightBlocked(attacker.position, target.position, opaqueObjects)) {
    return { hit: false, kind: "blocked", label: "blocked", reason: "line of sight blocked" };
  }
  return { hit: true, kind: "hit", label: "hit", reason: `${rule.damage} damage` };
}

function weaponRule(fixture, weaponId) {
  const rule = fixture.ruleset?.weapons?.[weaponId] ?? fixture.ruleset?.weapon ?? {};
  return {
    range: rule.range ?? 0,
    damage: rule.damage ?? 0,
    arc: rule.arc ?? "360",
  };
}

function markerId(weaponId) {
  if (weaponId === "fixed-railgun") return "arrow-railgun";
  if (weaponId === "training-laser") return "arrow-laser";
  return "arrow-mazer";
}

function marker(id, color) {
  const markerEl = svgEl("marker", {
    id,
    viewBox: "0 0 10 10",
    refX: "8",
    refY: "5",
    markerWidth: "5",
    markerHeight: "5",
    orient: "auto-start-reverse",
  });
  markerEl.appendChild(svgEl("path", {
    d: "M 0 0 L 10 5 L 0 10 z",
    fill: color,
  }));
  return markerEl;
}

function shipSprite(agent) {
  const point = axialToPixel(agent.position);
  const angle = vectorAngle(agent.facing ?? agent.velocity ?? { dq: 1, dr: 0 });
  const group = svgEl("g", {
    class: `ship ${agent.agent_id === "agent-a" ? "agent-a" : "agent-b"}`,
    "data-visual-object": "ship",
    "data-profile": "ship",
    "data-agent-id": agent.agent_id,
    "data-angle": angle.toFixed(6),
    "data-scale": String(SHIP_SCALE),
    transform: `translate(${point.x} ${point.y}) rotate(${angle}) scale(${SHIP_SCALE})`,
  });

  if (agent.weapons?.includes("fixed-railgun")) {
    group.appendChild(svgEl("polygon", {
      class: "arc-cone",
      points: "2,0 30,-9 30,9",
    }));
  }

  group.appendChild(svgEl("line", {
    class: "facing-ray",
    x1: "0",
    y1: "0",
    x2: "23",
    y2: "0",
  }));
  group.appendChild(svgEl("polygon", {
    class: "fin",
    points: "-3,-7 -13,-15 -10,-3",
  }));
  group.appendChild(svgEl("polygon", {
    class: "fin",
    points: "-3,7 -13,15 -10,3",
  }));
  group.appendChild(svgEl("polygon", {
    class: "engine-glow",
    points: "-18,-6 -26,0 -18,6",
  }));
  group.appendChild(svgEl("polygon", {
    class: "engine",
    points: "-16,-7 -23,0 -16,7",
  }));
  group.appendChild(svgEl("polygon", {
    class: "hull",
    points: "-18,-11 6,-12 21,-5 28,0 21,5 6,12 -18,11",
  }));
  group.appendChild(svgEl("polygon", {
    class: "nose",
    points: "18,-7 28,0 18,7",
  }));
  group.appendChild(svgEl("ellipse", {
    class: "cockpit",
    cx: "4",
    cy: "0",
    rx: "5",
    ry: "3",
  }));
  group.appendChild(svgEl("circle", {
    class: "side-port",
    cx: "-5",
    cy: "-7",
    r: "2.2",
  }));
  group.appendChild(svgEl("circle", {
    class: "side-port",
    cx: "-5",
    cy: "7",
    r: "2.2",
  }));

  const labelGroup = svgEl("g", {
    transform: `scale(${1 / SHIP_SCALE}) rotate(${-angle})`,
  });
  labelGroup.appendChild(svgText(agent.agent_id, 0, -40, "ship-label"));
  group.appendChild(labelGroup);
  return group;
}

function boardBounds(fixture, state) {
  const map = state.map ?? {};
  const definitionBounds = fixture.map_definition?.bounds ?? {};
  const positions = [
    ...state.agents.map((agent) => agent.position),
    ...mapObjects(fixture, state).map((object) => object.position),
  ];
  const qValues = positions.map((position) => position.q);
  const rValues = positions.map((position) => position.r);
  const qMin = map.q_min ?? definitionBounds.q_min ?? Math.min(...qValues, 0);
  const qMax = map.q_max ?? definitionBounds.q_max ?? Math.max(...qValues, 0);
  const rMin = map.r_min ?? definitionBounds.r_min ?? Math.min(...rValues, 0);
  const rMax = map.r_max ?? definitionBounds.r_max ?? Math.max(...rValues, 0);
  return { qMin, qMax, rMin, rMax };
}

function createBoardLayout(bounds) {
  const corners = [
    axialToPixel({ q: bounds.qMin, r: bounds.rMin }),
    axialToPixel({ q: bounds.qMin, r: bounds.rMax }),
    axialToPixel({ q: bounds.qMax, r: bounds.rMin }),
    axialToPixel({ q: bounds.qMax, r: bounds.rMax }),
  ];
  const xs = corners.map((point) => point.x);
  const ys = corners.map((point) => point.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return {
    minX,
    minY,
    width: maxX - minX,
    height: maxY - minY,
  };
}

function mapObjects(fixture, state) {
  return [
    ...(state.objects ?? []),
    ...(state.map?.objects ?? []),
    ...(fixture.map_definition?.objects ?? []),
  ].filter((object, index, objects) => {
    const id = object.id ?? `${object.type}-${object.position?.q}-${object.position?.r}`;
    return objects.findIndex((candidate) => (candidate.id ?? `${candidate.type}-${candidate.position?.q}-${candidate.position?.r}`) === id) === index;
  });
}

function axialToPixel(position) {
  return {
    x: HEX_SIZE * SQRT3 * (position.q + position.r / 2),
    y: HEX_SIZE * 1.5 * position.r,
  };
}

function vectorAngle(vector) {
  const origin = axialToPixel({ q: 0, r: 0 });
  const point = axialToPixel({ q: vector.dq ?? 1, r: vector.dr ?? 0 });
  return (Math.atan2(point.y - origin.y, point.x - origin.x) * 180) / Math.PI;
}

function hexPoints(cx, cy) {
  return Array.from({ length: 6 }, (_, index) => {
    const angle = (Math.PI / 180) * (60 * index - 30);
    return `${cx + HEX_SIZE * Math.cos(angle)},${cy + HEX_SIZE * Math.sin(angle)}`;
  }).join(" ");
}

function asteroidPoints(cx, cy) {
  return VISUAL_OBJECT_PROFILES.asteroid.map(([x, y]) => `${cx + x},${cy + y}`).join(" ");
}

function axialRangeRadius(fixture, weaponId) {
  return (weaponRule(fixture, weaponId).range || 0) * HEX_SIZE * 1.68;
}

function axialDistance(a, b) {
  const as = -a.q - a.r;
  const bs = -b.q - b.r;
  return (Math.abs(a.q - b.q) + Math.abs(a.r - b.r) + Math.abs(as - bs)) / 2;
}

function isAxialStraight(a, b) {
  return a.q === b.q || a.r === b.r || -a.q - a.r === -b.q - b.r;
}

function targetInForwardArc(attacker, target, distance) {
  const facing = attacker.facing;
  return Boolean(
    facing &&
      distance > 0 &&
      target.position.q - attacker.position.q === facing.dq * distance &&
      target.position.r - attacker.position.r === facing.dr * distance,
  );
}

function lineOfSightBlocked(attackerPosition, targetPosition, opaqueObjects) {
  const blockerPositions = new Set(opaqueObjects.map((object) => `${object.position.q},${object.position.r}`));
  return axialIntermediateLine(attackerPosition, targetPosition).some((position) => blockerPositions.has(`${position.q},${position.r}`));
}

function axialIntermediateLine(a, b) {
  if (a.r === b.r) {
    const step = b.q > a.q ? 1 : -1;
    return range(a.q + step, b.q, step).map((q) => ({ q, r: a.r }));
  }
  if (a.q === b.q) {
    const step = b.r > a.r ? 1 : -1;
    return range(a.r + step, b.r, step).map((r) => ({ q: a.q, r }));
  }
  const as = -a.q - a.r;
  const bs = -b.q - b.r;
  if (as === bs) {
    const qStep = b.q > a.q ? 1 : -1;
    const rStep = -qStep;
    const distance = Math.abs(b.q - a.q);
    return Array.from({ length: Math.max(0, distance - 1) }, (_, index) => ({
      q: a.q + qStep * (index + 1),
      r: a.r + rStep * (index + 1),
    }));
  }
  return [];
}

function range(start, end, step) {
  const values = [];
  for (let value = start; step > 0 ? value < end : value > end; value += step) {
    values.push(value);
  }
  return values;
}

function renderTimeline() {
  if (!selectedFixture) {
    elements.timeline.replaceChildren();
    return;
  }

  const max = selectedFixture.data.rounds.length;
  elements.timeline.replaceChildren(
    ...Array.from({ length: max + 1 }, (_, index) => {
      const markerButton = document.createElement("button");
      markerButton.type = "button";
      markerButton.className = index === currentRoundIndex ? "timeline-marker active" : "timeline-marker";
      markerButton.textContent = index === 0 ? "G" : String(index);
      markerButton.title = index === 0 ? "Genesis" : selectedFixture.data.rounds[index - 1]?.phase_note || `Round ${index}`;
      markerButton.addEventListener("click", () => setRound(index));
      return markerButton;
    }),
  );
}

function renderDiffList(previousState, state) {
  if (!previousState) {
    elements.diffList.replaceChildren(emptyCard("Genesis baseline; no previous round to diff."));
    return;
  }
  const previousAgents = new Map(previousState.agents.map((agent) => [agent.agent_id, agent]));
  const rows = [];
  for (const agent of state.agents) {
    const previous = previousAgents.get(agent.agent_id);
    if (!previous) continue;
    const changes = [
      diffField("position", coordText(previous.position, "q", "r"), coordText(agent.position, "q", "r")),
      diffField("velocity", coordText(previous.velocity, "dq", "dr"), coordText(agent.velocity, "dq", "dr")),
      diffField("HP", previous.hp, agent.hp),
      diffField("fuel", fuelFromState(previous, agent.agent_id), fuelForAgent(agent)),
    ].filter(Boolean);
    const card = document.createElement("article");
    card.className = "diff-card";
    card.innerHTML = `<h3>${escapeHtml(agent.agent_id)}</h3>${changes.length ? changes.map((change) => `<p>${change}</p>`).join("") : "<p>No tracked changes.</p>"}`;
    rows.push(card);
  }
  elements.diffList.replaceChildren(...rows);
}

function renderAuditDetails(audit) {
  elements.auditDetails.textContent = audit
    ? JSON.stringify(audit.final_audit ?? audit, null, 2)
    : "No audit sidecar loaded for this replay.";
}

function buildCollisionEvents(previousState, state) {
  if (!previousState) return [];
  const previousAgents = new Map(previousState.agents.map((agent) => [agent.agent_id, agent]));
  return state.agents
    .map((agent) => ({ agent, previous: previousAgents.get(agent.agent_id) }))
    .filter(({ agent, previous }) => previous && (agent.hp ?? 0) < (previous.hp ?? 0))
    .map(({ agent, previous }) => ({ agent, hpLost: (previous.hp ?? 0) - (agent.hp ?? 0) }));
}

function diffField(label, before, after) {
  return before === after ? null : `${escapeHtml(label)}: <strong>${escapeHtml(before)}</strong> → <strong>${escapeHtml(after)}</strong>`;
}

function coordText(value = {}, a, b) {
  return `${a}=${value?.[a] ?? 0}, ${b}=${value?.[b] ?? 0}`;
}

function fuelFromState(state, agentId) {
  if (!selectedFixture) return 0;
  if (state.round === 0) {
    const initial = selectedFixture.data.genesis.initial_ledger_payloads.find((item) => item.agent_id === agentId);
    return initial?.payload.initial_fuel ?? 0;
  }
  const round = selectedFixture.data.rounds[(state.round ?? 1) - 1];
  const input = round?.agent_inputs.find((item) => item.agent_id === agentId);
  return input?.ledger_payload.fuel_remaining ?? "hidden";
}

function playbackDelay() {
  return Math.max(80, Math.round(DEFAULT_PLAY_INTERVAL_MS / Number(elements.speedSelect.value || 1)));
}

function handleShortcut(event) {
  if (["INPUT", "SELECT", "TEXTAREA"].includes(event.target?.tagName)) return;
  if (event.key === "ArrowLeft") setRound(currentRoundIndex - 1);
  if (event.key === "ArrowRight") setRound(currentRoundIndex + 1);
  if (event.key.toLowerCase() === "r") setRound(0);
  if (event.key === " " || event.key.toLowerCase() === "k") {
    event.preventDefault();
    togglePlayback();
  }
}

async function copyCurrentHash() {
  const hash = elements.hashLabel.dataset.fullHash;
  if (!hash) return;
  await navigator.clipboard.writeText(hash);
  elements.copyHashButton.textContent = "Copied";
  window.setTimeout(() => {
    elements.copyHashButton.textContent = "Copy current hash";
  }, 900);
}

function fuelForAgent(agent) {
  const hash = agent.fuel_ledger_hash;
  if (!selectedFixture || currentRoundIndex === 0) {
    const initial = selectedFixture?.data.genesis.initial_ledger_payloads.find((item) => item.agent_id === agent.agent_id);
    return initial?.payload.initial_fuel ?? 0;
  }
  const input = selectedFixture.data.rounds[currentRoundIndex - 1].agent_inputs.find((item) => item.agent_id === agent.agent_id);
  return input?.ledger_payload.fuel_remaining ?? (hash ? "hidden" : 0);
}

function quorumText(round) {
  const quorum = round.quorum;
  if (!quorum) return "-";
  return quorum.locked ? `${quorum.votes_for_hash}/${quorum.active_agents} locked` : "not locked";
}

function shortHash(hash) {
  if (!hash) return "-";
  return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
}

function canonicalStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalStringify).join(",")}]`;
  }
  if (value && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalStringify(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function verifyObjectsContainedInHex() {
  const failures = [];
  const objects = [...document.querySelectorAll("[data-visual-object]")];

  for (const object of objects) {
    const profileName = object.dataset.profile;
    const profile = VISUAL_OBJECT_PROFILES[profileName] ?? [];
    const scale = Number(object.dataset.scale ?? 1);
    const angle = Number(object.dataset.angle ?? 0);
    const transformedPoints = profile.map(([x, y]) => rotatePoint(x * scale, y * scale, angle));
    const outsidePoints = transformedPoints.filter((point) => !pointInHex(point.x, point.y, HEX_SIZE - 2));

    if (outsidePoints.length > 0) {
      failures.push({
        id: object.dataset.agentId || object.dataset.objectId || profileName,
        type: object.dataset.visualObject,
        profile: profileName,
        outsidePoints,
      });
    }
  }

  return {
    ok: failures.length === 0,
    checked: objects.length,
    hexSize: HEX_SIZE,
    failures,
  };
}

function rotatePoint(x, y, angleDegrees) {
  const radians = (Math.PI / 180) * angleDegrees;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);
  return {
    x: x * cos - y * sin,
    y: x * sin + y * cos,
  };
}

function pointInHex(x, y, radius) {
  const vertices = hexLocalVertices(radius);
  let inside = false;
  for (let i = 0, j = vertices.length - 1; i < vertices.length; j = i, i += 1) {
    const a = vertices[i];
    const b = vertices[j];
    if ((a.y > y) !== (b.y > y) && x < ((b.x - a.x) * (y - a.y)) / (b.y - a.y) + a.x) {
      inside = !inside;
    }
  }
  return inside;
}

function hexLocalVertices(radius) {
  return Array.from({ length: 6 }, (_, index) => {
    const angle = (Math.PI / 180) * (60 * index - 30);
    return {
      x: radius * Math.cos(angle),
      y: radius * Math.sin(angle),
    };
  });
}

function svgEl(tagName, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tagName);
  for (const [key, value] of Object.entries(attributes)) {
    element.setAttribute(key, String(value));
  }
  return element;
}

function svgText(text, x, y, className) {
  const element = svgEl("text", { x, y, class: className });
  element.textContent = text;
  return element;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}
