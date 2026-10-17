/* All record content is rendered as text, never executable HTML. */
const $ = (id) => document.getElementById(id);
let session = "",
  catalog = null,
  label = "",
  view = "overview",
  offset = 0,
  total = 0,
  relation = "",
  detailId = "",
  detailOffset = 0,
  busy = false;
const limit = 50;
const readable = (name) =>
  (
    ({
      Action: "Actions · review packets",
      Campaign: "Campaigns · client programmes",
      Claim: "Claims · document statements",
      WorkItem: "Operational work items",
    })[name] || name
  )
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
    .replace(/([a-z])([A-Z])/g, "$1 $2");
const explanations = {
  Rule: "Accepted policy versions. Effective and recorded dates determine which version applies; a proposal cannot override them.",
  Claim:
    "What a document states. A statement can be outdated and does not override an accepted policy.",
  Receipt:
    "Saved investigations and their evidence snapshots. These are historical outputs, excluded from the agent's company-evidence tools.",
  Source:
    "Original excerpts, tickets, chats and public references. Open a record to read its text, classification, content hash and connections.",
  Action:
    "Local drafts prepared for human review. These are not externally published actions.",
  Campaign:
    "A client promotion or logistics rollout with dates, regions and planning volumes. It explains demand and capacity decisions; ending a programme does not automatically change a contract.",
  WorkItem:
    "Pending operational work connected to a client, review ticket, owner and assigned role. These differ from saved investigation review packets in Action.",
  Shipment:
    "Consignments linked to clients, warehouse pickups, routes and processing facilities. Operational snapshots and the planned scheduling cohort are separate.",
};
const el = (tag, text, cls) => {
  const n = document.createElement(tag);
  if (text !== undefined)
    n.textContent =
      typeof text === "object" ? JSON.stringify(text) : String(text);
  if (cls) n.className = cls;
  return n;
};
const value = (v) =>
  v === undefined
    ? "—"
    : v === null
      ? "null"
      : typeof v === "object"
        ? JSON.stringify(v)
        : String(v);
function message(text, error = false) {
  $("message").textContent = text;
  $("message").setAttribute("role", error ? "alert" : "status");
}
async function api(operation, body = {}) {
  const r = await fetch("/api/database/" + operation, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: session, ...body }),
  });
  if (!r.ok) {
    let d;
    try {
      d = await r.json();
    } catch {}
    throw new Error(
      typeof d?.detail === "string"
        ? d.detail
        : "Database request failed. Please retry.",
    );
  }
  return r.json();
}
async function task(fn) {
  if (busy) return;
  busy = true;
  message("Reading FalkorDB…");
  try {
    await fn();
    if ($("message").textContent === "Reading FalkorDB…") message("");
  } catch (e) {
    message(e.message, true);
  } finally {
    busy = false;
  }
}
function table(columns, rows, cell) {
  const wrap = el("div", undefined, "table-wrap"),
    t = el("table"),
    head = el("thead"),
    hr = el("tr");
  for (const c of columns) {
    const th = el("th", c.replaceAll("_", " "));
    th.dataset.column = c;
    hr.append(th);
  }
  head.append(hr);
  t.append(head);
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    for (const c of columns) {
      const td = el("td");
      td.dataset.column = c;
      const custom = cell?.(c, row);
      const preview = el("span", value(row[c]), "cell-preview");
      preview.title = value(row[c]);
      td.append(custom || preview);
      tr.append(td);
    }
    body.append(tr);
  }
  t.append(body);
  wrap.append(t);
  return wrap;
}
function link(id, title) {
  const b = el("button", title || id, "link cell-preview");
  b.title = id;
  b.setAttribute("aria-label", "Inspect " + (title || id));
  b.onclick = () => task(() => inspect(id));
  return b;
}
async function connect(fresh = false) {
  const id = fresh ? "" : $("workspace").value.trim();
  if (!fresh && !/^[a-f0-9]{32}$/.test(id))
    throw new Error("Enter a valid workspace ID, or create a workspace.");
  const r = await fetch("/api/company/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: id || null }),
  });
  if (!r.ok) {
    const d = await r.json();
    throw new Error(
      typeof d.detail === "string" ? d.detail : "Unable to open workspace",
    );
  }
  const data = await r.json();
  session = data.session_id;
  $("workspace").value = session;
  localStorage.setItem("chronos-inspection-session", session);
  history.replaceState(null, "", "#workspace=" + session);
  $("browser").hidden = false;
  await refresh();
  $("connect").hidden = true;
}
async function refresh() {
  catalog = await api("catalog");
  const priority = [
    "Company",
    "Client",
    "Team",
    "Person",
    "Decision",
    "Source",
    "Ticket",
    "Rule",
    "Policy",
    "Claim",
    "Facility",
  ];
  catalog.labels.sort(
    (a, b) =>
      (priority.includes(a.label) ? priority.indexOf(a.label) : 99) -
        (priority.includes(b.label) ? priority.indexOf(b.label) : 99) ||
      a.label.localeCompare(b.label),
  );
  $("totals").textContent =
    `${catalog.records.toLocaleString()} records · ${catalog.connections.toLocaleString()} relationships · schema v${catalog.metadata.schema_version} · knowledge revision ${catalog.metadata.revision}`;
  $("workspace-title").textContent =
    catalog.company?.title || "Workspace " + session.slice(0, 8);
  $("disclosure").textContent = catalog.disclosure;
  $("tables").replaceChildren();
  const groups = [
    [
      "Company knowledge",
      (x) =>
        ![
          "Shipment",
          "ScanEvent",
          "Manifest",
          "Route",
          "PickupRequest",
          "Return",
          "DeliveryException",
          "CODCollection",
          "Remittance",
          "Invoice",
          "Vehicle",
          "Receipt",
          "Action",
          "Event",
          "Metadata",
        ].includes(x.label),
    ],
    [
      "Operations & finance",
      (x) =>
        [
          "Shipment",
          "ScanEvent",
          "Manifest",
          "Route",
          "PickupRequest",
          "Return",
          "DeliveryException",
          "CODCollection",
          "Remittance",
          "Invoice",
          "Vehicle",
        ].includes(x.label),
    ],
    [
      "Investigation history & setup",
      (x) => ["Receipt", "Action", "Event", "Metadata"].includes(x.label),
    ],
  ];
  for (const [name, matches] of groups) {
    $("tables").append(el("p", name, "nav-group"));
    for (const item of catalog.labels.filter(matches)) {
      const b = el("button", readable(item.label));
      b.dataset.label = item.label;
      b.append(el("span", item.count.toLocaleString()));
      b.classList.toggle("active", label === item.label);
      b.onclick = () =>
        task(async () => {
          label = item.label;
          view = "records";
          offset = 0;
          $("search").value = "";
          await render();
        });
      $("tables").append(b);
    }
  }
  if (!label)
    label =
      catalog.labels.find((x) => x.label === "Company")?.label ||
      catalog.labels[0]?.label ||
      "";
  const types = [...new Set(catalog.relationships.map((r) => r.type))];
  $("relation").replaceChildren(
    new Option("All relationship types", ""),
    ...types.map((t) => new Option(t, t)),
  );
  $("relation").value = relation;
  await render();
}
async function render() {
  document
    .querySelectorAll("[data-view]")
    .forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  [...$("tables").children].forEach((b) =>
    b.classList.toggle(
      "active",
      view === "records" && b.dataset.label === label,
    ),
  );
  $("search-form").hidden = !["records", "relationships"].includes(view);
  $("search").hidden = view !== "records";
  $("search-form").querySelector("button").hidden = view !== "records";
  $("relation").hidden = view !== "relationships";
  $("pagination").hidden = !["records", "relationships"].includes(view);
  $("content").replaceChildren();
  $("table-title").textContent =
    view === "overview"
      ? "Start your review"
      : view === "records"
        ? readable(label)
        : view === "relationships"
          ? "Relationships"
          : view === "schema"
            ? "Live schema & enforcement"
            : "Structural integrity";
  $("count").textContent = "";
  if (view === "overview") {
    const intro = el("section", undefined, "review-intro");
    intro.append(
      el("h3", "Follow a record. Check its evidence. Verify the answer."),
      el(
        "p",
        "Browse company knowledge or operational records on the left. Open any record to inspect every field and follow its real connections. Nothing is hidden by the compact table previews.",
      ),
    );
    $("content").append(intro);
    const grid = el("div", undefined, "overview-grid");
    for (const item of catalog.labels.filter(
      (x) => !["Metadata", "Receipt", "Action", "Event"].includes(x.label),
    )) {
      const card = el("button", undefined, "overview-card secondary");
      card.append(
        el("strong", item.count.toLocaleString()),
        el("span", readable(item.label)),
        el(
          "small",
          Object.keys(item.fields).length + " fields · explore records →",
        ),
      );
      card.onclick = () =>
        task(async () => {
          label = item.label;
          view = "records";
          offset = 0;
          $("search").value = "";
          await render();
        });
      grid.append(card);
    }
    $("content").append(grid);
    const note = el("section", undefined, "schema-card");
    note.append(
      el("h3", "What is stored here?"),
      el(
        "p",
        "Business records are connected in FalkorDB. Receipts preserve previous investigations; they are historical outputs, not answers fed back as company facts. Actions are review packets created from investigations. Operational work items are tracked separately. Metadata stores schema versions and walkthrough controls, not prewritten answers.",
      ),
      el(
        "p",
        "Use Schema & indexes for observed fields and database enforcement, Integrity checks for structural validation, or Download full JSON for the complete snapshot.",
      ),
    );
    $("content").append(note);
  } else if (view === "records") {
    if (explanations[label])
      $("content").append(el("p", explanations[label], "record-explanation"));
    const data = await api("rows", {
      label,
      query: $("search").value,
      offset,
      limit,
    });
    total = data.total;
    const fields = catalog.labels.find((x) => x.label === label)?.fields || {};
    const preferred = [
      "id",
      "title",
      "status",
      "mode",
      "created_at",
      "revision",
      "schema_version",
      "client",
      "department",
      "source_type",
      "timestamp",
      "enabled",
      "city",
      "field",
      "value",
      "event_at",
      "arrival_at",
    ];
    // Keep large documents, nested objects and runtime payloads out of row previews.
    // All values remain available in the record inspector and JSON export.
    const columns = [
      "title",
      ...preferred.filter((k) => k !== "id" && k !== "title" && k in fields),
    ].slice(0, 5);
    const rows = data.rows.map((r) => r.record);
    $("content").append(
      table(columns, rows, (c, r) =>
        c === "title" ? link(r.id, r.title || r.id) : null,
      ),
    );
    if (label === "Metadata")
      $("content").prepend(
        el(
          "p",
          "Workspace configuration: guided questions and replay controls, not model answers. Open the dataset record to see the complete configuration.",
          "note",
        ),
      );
    if (!rows.length)
      $("content").append(
        el("p", "No matching records. Clear the search to browse every row."),
      );
    $("count").textContent =
      total.toLocaleString() +
      " records · open a record for all fields and connections";
  } else if (view === "relationships") {
    const data = await api("relationships", { relation, offset, limit });
    total = data.total;
    $("content").append(edgeTable(data.rows));
    $("count").textContent = total.toLocaleString() + " relationships";
  } else if (view === "schema") {
    for (const [title, rows] of [
      ["Database constraints", catalog.constraints],
      ["Range indexes", catalog.indexes],
      ["Relationship endpoint types", catalog.relationships],
    ]) {
      const card = el("section", undefined, "schema-card");
      card.append(el("h3", title));
      card.append(
        rows.length
          ? table(Object.keys(rows[0]), rows)
          : el("p", "None present."),
      );
      $("content").append(card);
    }
    const fields = catalog.labels.find((x) => x.label === label);
    if (fields) {
      const card = el("section", undefined, "schema-card");
      card.append(
        el("h3", label + " · all observed fields"),
        el(
          "p",
          "Observed schema describes stored data. Only the constraints listed above are database-enforced.",
        ),
        table(
          ["field", "types", "native"],
          Object.entries(fields.fields).map(([field, types]) => ({
            field,
            types,
            native: fields.native_fields.includes(field)
              ? "yes"
              : "JSON payload",
          })),
        ),
      );
      $("content").append(card);
    }
  } else {
    const audit = await api("audit");
    $("content").append(
      el(
        "p",
        audit.passed
          ? "All implemented structural checks passed."
          : "Some checks found violations.",
        audit.passed ? "pass" : "fail",
      ),
      el("p", audit.scope),
      table(["name", "violations", "passed"], audit.checks),
      el("p", "Checked at " + audit.checked_at),
    );
  }
  $("previous").disabled = offset === 0;
  $("next").disabled = offset + limit >= total;
  $("page").textContent = total
    ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total.toLocaleString()}`
    : "0 records";
}
function edgeTable(rows) {
  return table(["source", "relation", "target", "properties"], rows, (c, r) =>
    c === "source" || c === "target"
      ? link(r[c], r[c + "_title"] || r[c])
      : null,
  );
}
async function inspect(id) {
  detailId = id;
  detailOffset = 0;
  const data = await api("record", { record_id: id });
  $("detail-title").textContent =
    data.label + " · " + (data.record.title || id);
  const dl = el("dl", undefined, "field-list");
  const provenance = {};
  for (const [k, v] of Object.entries(data.record)) {
    if (["synthetic", "classification", "content_hash"].includes(k)) {
      provenance[k] = v;
      continue;
    }
    const dd = el("dd");
    if (typeof v === "object" && v !== null) {
      const disclosure = el("details");
      disclosure.append(
        el(
          "summary",
          Array.isArray(v)
            ? `${v.length} items · expand`
            : "Structured data · expand",
        ),
        el("pre", JSON.stringify(v, null, 2)),
      );
      dd.append(disclosure);
    } else dd.append(el("span", value(v)));
    dl.append(el("dt", k.replaceAll("_", " ")), dd);
  }
  $("detail-body").replaceChildren(dl);
  const provenanceDetails = el("details");
  provenanceDetails.append(
    el("summary", "Provenance & record classification"),
    el("pre", JSON.stringify(provenance, null, 2)),
  );
  $("detail-body").append(provenanceDetails);
  const native = el("details");
  native.append(
    el("summary", "Native database properties"),
    el("pre", JSON.stringify(data.properties, null, 2)),
  );
  $("detail-body").append(native, el("h3", "Direct relationships"));
  const connections = el("div");
  connections.id = "detail-edges";
  $("detail-body").append(connections);
  await detailEdges();
  if (!$("detail").open) $("detail").showModal();
}
async function detailEdges() {
  const data = await api("relationships", {
    record_id: detailId,
    offset: detailOffset,
    limit: 20,
  });
  const box = $("detail-edges");
  box.replaceChildren(edgeTable(data.rows));
  const controls = el("div", undefined, "controls"),
    prev = el("button", "Previous", "secondary"),
    next = el("button", "Next", "secondary");
  prev.disabled = !detailOffset;
  next.disabled = detailOffset + 20 >= data.total;
  prev.onclick = () =>
    task(async () => {
      detailOffset -= 20;
      await detailEdges();
    });
  next.onclick = () =>
    task(async () => {
      detailOffset += 20;
      await detailEdges();
    });
  controls.append(
    prev,
    el(
      "span",
      `${data.total} relationships · page ${Math.floor(detailOffset / 20) + 1}`,
    ),
    next,
  );
  box.append(controls);
}
$("connect-form").onsubmit = (e) => {
  e.preventDefault();
  task(() => connect());
};
$("new").onclick = () => task(() => connect(true));
$("refresh").onclick = () => task(refresh);
$("search-form").onsubmit = (e) => {
  e.preventDefault();
  offset = 0;
  task(render);
};
$("relation").onchange = () => {
  relation = $("relation").value;
  offset = 0;
  task(render);
};
$("previous").onclick = () => {
  offset = Math.max(0, offset - limit);
  task(render);
};
$("next").onclick = () => {
  offset += limit;
  task(render);
};
document.querySelectorAll("[data-view]").forEach(
  (b) =>
    (b.onclick = () =>
      task(async () => {
        view = b.dataset.view;
        offset = 0;
        await render();
      })),
);
$("close").onclick = () => $("detail").close();
$("share").onclick = () =>
  task(async () => {
    await navigator.clipboard.writeText(location.href);
    message("Inspection link copied. It grants read access to this workspace.");
  });
$("export").onclick = () =>
  task(async () => {
    const data = await api("export");
    const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      }),
      url = URL.createObjectURL(blob),
      a = el("a");
    a.href = url;
    a.download = "chronos-workspace-" + session.slice(0, 8) + ".json";
    a.click();
    URL.revokeObjectURL(url);
  });
const supplied =
  new URLSearchParams(location.hash.slice(1)).get("workspace") ||
  localStorage.getItem("chronos-inspection-session");
if (supplied) {
  $("workspace").value = supplied;
  task(() => connect());
}

$("change").onclick = () => {
  $("connect").hidden = false;
  $("workspace").focus();
};
