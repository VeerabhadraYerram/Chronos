/* All record content is rendered as text, never executable HTML. */
const $ = (id) => document.getElementById(id);
let session = "",
  catalog = null,
  label = "",
  view = "records",
  offset = 0,
  total = 0,
  relation = "",
  detailId = "",
  detailOffset = 0,
  busy = false;
const limit = 50;
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
    const th = el("th", c);
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
      td.append(custom || el("span", value(row[c])));
      tr.append(td);
    }
    body.append(tr);
  }
  t.append(body);
  wrap.append(t);
  return wrap;
}
function link(id, title) {
  const b = el("button", title || id, "link");
  b.onclick = () => task(() => inspect(id));
  return b;
}
async function connect(fresh = false) {
  const id = fresh ? "" : $("workspace").value.trim();
  if (!fresh && !/^[a-f0-9]{32}$/.test(id))
    throw new Error("Enter a valid workspace ID, or create a demo workspace.");
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
  $("totals").textContent =
    `${catalog.records.toLocaleString()} records · ${catalog.connections.toLocaleString()} relationships · schema v${catalog.metadata.schema_version} · knowledge revision ${catalog.metadata.revision}`;
  $("workspace-title").textContent =
    catalog.company?.title || "Workspace " + session.slice(0, 8);
  $("disclosure").textContent = catalog.disclosure;
  $("tables").replaceChildren();
  for (const item of catalog.labels) {
    const b = el("button", item.label);
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
    b.classList.toggle("active", b.firstChild.textContent === label),
  );
  $("search-form").hidden = !["records", "relationships"].includes(view);
  $("search").hidden = view !== "records";
  $("search-form").querySelector("button").hidden = view !== "records";
  $("relation").hidden = view !== "relationships";
  $("pagination").hidden = !["records", "relationships"].includes(view);
  $("content").replaceChildren();
  $("table-title").textContent =
    view === "records"
      ? label
      : view === "relationships"
        ? "Relationships"
        : view === "schema"
          ? "Live schema & enforcement"
          : "Structural integrity";
  $("count").textContent = "";
  if (view === "records") {
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
    const columns = [
      ...new Set([
        ...preferred.filter((k) => k in fields),
        ...Object.keys(fields).filter(
          (k) =>
            ![
              "excerpt",
              "description",
              "search_text",
              "payload",
              "kind",
              "content_hash",
              "synthetic",
            ].includes(k),
        ),
      ]),
    ].slice(0, 8);
    const rows = data.rows.map((r) => r.record);
    $("content").append(
      table(columns, rows, (c, r) => (c === "id" ? link(r.id) : null)),
    );
    if (!rows.length)
      $("content").append(
        el("p", "No matching records. Clear the search to browse every row."),
      );
    $("count").textContent =
      total.toLocaleString() + " records · select an ID for all fields";
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
      ? link(r[c], r[c] + " · " + r[c + "_title"])
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
  for (const [k, v] of Object.entries(data.record)) {
    dl.append(el("dt", k), el("dd", value(v)));
  }
  $("detail-body").replaceChildren(dl);
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
    message(
      "Inspection link copied. It grants read access to this demo workspace.",
    );
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
