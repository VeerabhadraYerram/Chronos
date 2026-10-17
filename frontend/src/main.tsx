import CompanyWorkspace from "./CompanyWorkspace";
import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  type NodeProps,
} from "@xyflow/react";
import {
  Activity,
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Box,
  Braces,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Clock3,
  Copy,
  Database,
  FileCode2,
  FileText,
  FlaskConical,
  GitBranch,
  GitPullRequest,
  History,
  Layers3,
  Link2,
  LoaderCircle,
  MessageSquare,
  Maximize2,
  Network,
  Play,
  Plus,
  Radio,
  Search,
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Terminal,
  Users,
  X,
  Zap,
} from "lucide-react";
import "@xyflow/react/dist/style.css";
import "./design-system.css";
import { api } from "./api";
import type {
  Action,
  Check as PartnerCheck,
  Entity,
  Graph,
  Receipt,
  Rehearsal,
} from "./types";

const KIND_COLORS: Record<string, string> = {
  System: "#5277c4",
  File: "#68798c",
  Decision: "#c7813f",
  FactVersion: "#c7813f",
  Source: "#3a8d7b",
  Commitment: "#9271b9",
  Person: "#5277c4",
  Document: "#3a8d7b",
  Team: "#5277c4",
  Project: "#9271b9",
  Ticket: "#b66a61",
};
const icons: Record<string, typeof Box> = {
  System: Box,
  File: FileCode2,
  Decision: GitBranch,
  FactVersion: GitBranch,
  Source: MessageSquare,
  Commitment: ShieldCheck,
  Person: Users,
  Document: BookOpen,
  Team: Users,
  Project: Layers3,
  Ticket: GitPullRequest,
};
const statusLabel = (value: string) =>
  ({
    conflict: "Conflict found",
    no_known_conflict: "No known conflict",
    insufficient_evidence: "Evidence incomplete",
  })[value] || value;
const dateLabel = (value?: string) =>
  value
    ? new Date(value).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      })
    : "Open-ended";

function GraphNode({ data }: NodeProps) {
  const entity = data.entity as Entity;
  const Icon = icons[entity.kind] || Box;
  const color = KIND_COLORS[entity.kind] || "#9aa89e";
  return (
    <div
      className={
        "graph-node " +
        (data.highlight ? "highlight " : "") +
        (entity.enabled === false ? "is-withdrawn" : "")
      }
      style={{ "--node-color": color } as React.CSSProperties}
      role="button"
      tabIndex={0}
      aria-label={`${entity.kind}: ${entity.title}`}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.currentTarget.click();
        }
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div className="node-type">
        <span className="node-icon">
          <Icon size={15} />
        </span>
        {entity.kind === "FactVersion"
          ? "CONSTRAINT"
          : entity.kind.toUpperCase()}
      </div>
      <strong>{entity.title}</strong>
      <span>
        {entity.kind === "Source"
          ? entity.enabled === false
            ? "Withdrawn evidence"
            : entity.source_type
          : entity.kind === "Person"
            ? entity.role
            : entity.kind === "FactVersion"
              ? `${entity.status} · ${entity.partner?.toUpperCase()}`
              : "NovaPay company knowledge"}
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { company: GraphNode };

function EvidenceGraph({
  graph,
  onSelect,
  highlight,
}: {
  graph: Graph;
  onSelect: (entity: Entity) => void;
  highlight?: string;
}) {
  const [width, setWidth] = useState(window.innerWidth);
  useEffect(() => {
    const resize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);
  const { nodes, edges } = useMemo(() => {
    const main = graph.nodes.filter(
      (n) => !["Event", "Team", "Project", "Ticket"].includes(n.kind),
    );
    const columns: Record<string, number> = {
      Person: 0,
      File: 0,
      System: 1,
      Decision: 2,
      Document: 2,
      FactVersion: 3,
      Source: 4,
      Commitment: 4,
    };
    const counts: Record<number, number> = {};
    const layout: Record<string, [number, number]> = {
      "file-worker": [0, 0],
      "system-payments": [1, 0],
      "decision-retry": [2, 0],
      "person-maya": [0, 1],
      "fact-a-original": [1, 1],
      "fact-a-historical": [1, 1],
      "fact-b-original": [2, 1],
      "fact-b-historical": [2, 1],
      "fact-b-migrated": [2, 1],
      "source-incident": [0, 2],
      "commitment-a": [1, 2],
      "commitment-b": [2, 2],
      "source-migration": [0, 3],
      "doc-retry": [0, 4],
      "doc-claim-a": [1, 4],
      "doc-claim-b": [2, 4],
      "source-runbook": [0, 5],
      "source-chat": [1, 5],
      "person-leo": [2, 5],
      "system-checkout": [0, 6],
    };
    const used = new Set<string>();
    const nodes = main.map((n) => {
      let [col, row] = layout[n.id] || [
        columns[n.kind] ?? 2,
        (counts[columns[n.kind] ?? 2] || 0) + 7,
      ];
      while (used.has(col + "," + row)) row += 3;
      used.add(col + "," + row);
      counts[col] = (counts[col] || 0) + 1;
      return {
        id: n.id,
        type: "company",
        position: { x: col * 235, y: row * 145 },
        data: { entity: n, highlight: highlight === n.id },
        draggable: true,
      };
    });
    const ids = new Set(nodes.map((n) => n.id));
    const edges = graph.edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e, i) => ({
        id: "edge-" + i,
        source: e.source,
        target: e.target,
        label: e.relation.replaceAll("_", " ").toLowerCase(),
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#abb4c0" },
        style: {
          stroke:
            highlight && (e.source === highlight || e.target === highlight)
              ? "#cc7c42"
              : "#b8c1cc",
          strokeWidth: 1.5,
        },
        labelStyle: { fill: "#697789", fontSize: 10 },
        labelBgStyle: { fill: "#f7f9fc" },
        labelBgPadding: [5, 3] as [number, number],
      }));
    return { nodes, edges };
  }, [graph, highlight]);
  return (
    <ReactFlow
      key={nodes.map((n) => n.id).join(",") + width}
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, n) => onSelect(n.data.entity)}
      fitView
      fitViewOptions={{ padding: 0.16 }}
      minZoom={0.25}
      maxZoom={1.4}
      nodesConnectable={false}
      colorMode="light"
      proOptions={{ hideAttribution: false }}
    >
      <Background color="#d7dee7" gap={22} size={1} />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}

function PartnerResult({ check }: { check: PartnerCheck }) {
  return (
    <div className={"partner-result " + check.status}>
      <div>
        <span className="partner-avatar">{check.partner.toUpperCase()}</span>
        <div>
          <strong>Partner {check.partner.toUpperCase()}</strong>
          <small>
            {check.minimum_ms === null
              ? "Missing accepted evidence"
              : `Accepted minimum: ${check.minimum_ms} ms`}
          </small>
        </div>
      </div>
      <span className="status-dot" title={statusLabel(check.status)}>
        {check.status === "no_known_conflict" ? (
          <Check size={15} />
        ) : check.status === "conflict" ? (
          <ShieldAlert size={15} />
        ) : (
          <CircleHelp size={15} />
        )}
      </span>
    </div>
  );
}

function App() {
  const [health, setHealth] = useState<{
    connected: boolean;
    revision: number;
    gemini_configured: boolean;
    gemini_model: string;
  } | null>(null);
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [tab, setTab] = useState("investigate");
  const [question, setQuestion] = useState(
    "Can we remove the 250 ms retry delay from the payment worker?",
  );
  const [partner, setPartner] = useState("all");
  const [delay, setDelay] = useState(0);
  const [effective, setEffective] = useState("2026-10-15");
  const [known, setKnown] = useState("2026-10-15");
  const [gemini, setGemini] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<Entity | null>(null);
  const [modal, setModal] = useState("");
  const [history, setHistory] = useState<Receipt[]>([]);
  const [action, setAction] = useState<Action | null>(null);
  const [rehearsal, setRehearsal] = useState<Rehearsal | null>(null);
  const [graphScope, setGraphScope] = useState("decision");
  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (selected) setSelected(null);
        else setModal("");
      }
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [selected]);
  const request = {
    question,
    partner,
    proposed_ms: delay,
    effective_at: effective + "T12:00:00Z",
    known_at: known + "T12:00:00Z",
    use_gemini: gemini,
  };
  const changed =
    receipt &&
    ["question", "partner", "proposed_ms", "effective_at", "known_at"].some(
      (k) => receipt.request[k] !== request[k as keyof typeof request],
    );
  const refresh = async () => {
    const h = await api<typeof health & {}>("/health");
    setHealth(h);
    if (h.connected) setGraph(await api<Graph>("/graph"));
    return h;
  };
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!notice) return;
    const timer = setTimeout(() => setNotice(""), 6000);
    return () => clearTimeout(timer);
  }, [notice]);
  async function task(name: string, fn: () => Promise<void>) {
    setBusy(name);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy("");
    }
  }
  async function investigate() {
    await task("investigate", async () => {
      const result = await api<Receipt>("/investigate", request);
      setReceipt(result);
      setAction(null);
      await refresh();
    });
  }
  async function replay(event: string) {
    await task(event, async () => {
      const result = await api<{ message: string }>("/events/replay", {
        event,
      });
      setNotice(result.message);
      await refresh();
      if (receipt) setReceipt({ ...receipt, stale: true });
      setRehearsal(null);
    });
  }
  async function openHistory() {
    await task("history", async () => {
      setHistory(await api<Receipt[]>("/receipts"));
      setModal("receipts");
    });
  }
  async function prepare() {
    if (!receipt) return;
    await task("repair", async () => {
      setAction(await api<Action>(`/receipts/${receipt.id}/repair`, {}));
      setModal("repair");
    });
  }
  const contextGraph = useMemo(() => {
    // This is a display filter only. Assessments always come from the API.
    const ids = new Set(
      graph.nodes
        .filter(
          (n) =>
            n.kind === "FactVersion" &&
            n.status === "accepted" &&
            String(n.valid_from) <= request.effective_at &&
            (!n.valid_to || request.effective_at < String(n.valid_to)) &&
            String(n.recorded_from) <= request.known_at &&
            (!n.recorded_to || request.known_at < String(n.recorded_to)),
        )
        .map((n) => n.id),
    );
    for (const edge of graph.edges) {
      if (
        ids.has(edge.source) &&
        ["SUPPORTED_BY", "GOVERNED_BY"].includes(edge.relation)
      )
        ids.add(edge.target);
      if (ids.has(edge.target) && edge.relation === "HAS_VERSION")
        ids.add(edge.source);
    }
    for (const edge of graph.edges)
      if (ids.has(edge.source) && edge.relation === "APPLIES_TO")
        ids.add(edge.target);
    for (const edge of graph.edges)
      if (ids.has(edge.target) && ["OWNS", "PART_OF"].includes(edge.relation))
        ids.add(edge.source);
    return {
      nodes: graph.nodes.filter((n) => ids.has(n.id)),
      edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
    };
  }, [graph, request.effective_at, request.known_at]);
  const visibleGraph =
    graphScope === "all"
      ? graph
      : tab === "investigate" && receipt && !receipt.stale
        ? receipt.graph
        : contextGraph;
  const facts = graph.nodes.filter(
    (n) => n.kind === "FactVersion" && n.status === "accepted",
  );
  const sources = graph.nodes.filter((n) => n.kind === "Source");
  const events = [
    {
      id: "migration",
      title: "Partner B migration",
      sub: "Approved decision · effective 10 Oct",
      icon: GitBranch,
    },
    {
      id: "proposal",
      title: "Unapproved suggestion",
      sub: "Chat export · preserve approval boundary",
      icon: MessageSquare,
    },
    {
      id: "withdraw-evidence",
      title: "Withdraw incident evidence",
      sub: "Evidence challenge · test abstention",
      icon: ShieldAlert,
    },
  ];
  const eventApplied = (id: string) =>
    graph.nodes.some((n) => n.id === "event-" + id);
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="ChronosGraph home">
          <span className="brand-symbol">
            <Network size={22} />
          </span>
          <span>
            chronos<span className="brand-light">graph</span>
            <small>COMPANY DECISION MEMORY</small>
          </span>
        </a>
        <div className="workspace-switch">
          <span className="company-avatar">N</span>
          <div>
            NovaPay<small>Demo workspace</small>
          </div>
          <ChevronDown size={13} />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav>
          <button
            className={
              !modal && tab !== "rehearse" ? "nav-item active" : "nav-item"
            }
            onClick={() => {
              setModal("");
              setTab("investigate");
            }}
          >
            <Network size={17} />
            Investigations
          </button>
          <button
            className={"nav-item " + (modal === "sources" ? "active" : "")}
            onClick={() => setModal("sources")}
          >
            <BookOpen size={17} />
            Knowledge sources<span className="nav-count">{sources.length}</span>
          </button>
          <button
            className={"nav-item " + (modal === "receipts" ? "active" : "")}
            onClick={openHistory}
            disabled={!!busy}
          >
            <History size={17} />
            Decision receipts
          </button>
          <button
            className={
              "nav-item " + (tab === "rehearse" && !modal ? "active" : "")
            }
            onClick={() => {
              setTab("rehearse");
              setModal("");
            }}
          >
            <FlaskConical size={17} />
            Rehearsal lab
          </button>
        </nav>
        <div className="sidebar-note">
          <span className="eyebrow">
            <Radio size={12} />
            GRAPH HACKS 2026
          </span>
          <strong>Built for Company Brain.</strong>
          <p>People, decisions, and evidence. Connected through time.</p>
          <a
            href="https://www.wemakedevs.org/hackathons/falkordb#tracks"
            target="_blank"
            rel="noreferrer"
          >
            Competition brief <ArrowUpRight size={12} />
          </a>
        </div>
        <div className="sidebar-bottom">
          <div className="database-state">
            <span className={"dot " + (health?.connected ? "green" : "")} />
            <span>
              FalkorDB
              <small>
                {health?.connected
                  ? "Connected locally"
                  : "Waiting for database"}
              </small>
            </span>
            <Database size={15} />
          </div>
          <button className="nav-item" onClick={() => setModal("setup")}>
            <CircleHelp size={16} />
            Setup & scope
          </button>
          <div className="profile">
            <span className="profile-avatar">
              <Users size={16} />
            </span>
            <span>
              NovaPay investigator<small>Local development</small>
            </span>
          </div>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="breadcrumbs">
            Workspace <ChevronRight size={12} /> NovaPay{" "}
            <ChevronRight size={12} />
            <strong>Investigations</strong>
          </div>
          <div className="topbar-right">
            <span className="demo-badge">
              <span className="dot" />
              SYNTHETIC DATA
            </span>
            <button
              className="icon-button"
              onClick={() => setModal("setup")}
              aria-label="Open setup and scope"
            >
              <CircleHelp size={17} />
            </button>
          </div>
        </header>
        <div className="main-content">
          <section className="page-heading">
            <div>
              <div className="eyebrow">
                <span className="tiny-line" />
                COMPANY INTELLIGENCE / INVESTIGATIONS
              </div>
              <h1>
                Clarity before every change<span>.</span>
              </h1>
              <p>
                Connect the decision. Follow the evidence. Understand what comes
                next.
              </p>
            </div>
            <button
              className="secondary-button"
              onClick={openHistory}
              disabled={!!busy}
            >
              <History size={15} />
              Saved receipts <ArrowUpRight size={14} />
            </button>
          </section>
          <section className="metrics-strip">
            <div>
              <span className="metric-icon blue">
                <Network size={17} />
              </span>
              <span>
                <strong>{graph.nodes.length || "—"}</strong>
                <small>Company entities</small>
              </span>
            </div>
            <div>
              <span className="metric-icon amber">
                <GitBranch size={17} />
              </span>
              <span>
                <strong>{facts.length || "—"}</strong>
                <small>Accepted fact versions</small>
              </span>
            </div>
            <div>
              <span className="metric-icon mint">
                <Link2 size={17} />
              </span>
              <span>
                <strong>{sources.length || "—"}</strong>
                <small>Traceable sources</small>
              </span>
            </div>
            <div>
              <span className="metric-icon violet">
                <Layers3 size={17} />
              </span>
              <span>
                <strong>
                  {health?.revision
                    ? String(health.revision).padStart(2, "0")
                    : "—"}
                </strong>
                <small>Knowledge revision</small>
              </span>
            </div>
            <div className="powered">
              <Database size={16} />
              <span>
                CONTEXT POWERED BY<strong>FalkorDB</strong>
              </span>
            </div>
          </section>
          {error && (
            <div className="alert error" role="alert">
              <ShieldAlert size={17} />
              <span>{error}</span>
              <button onClick={() => setError("")} aria-label="Dismiss error">
                <X size={14} />
              </button>
            </div>
          )}
          {notice && (
            <div className="alert notice" role="status">
              <CheckCheck size={17} />
              <span>{notice}</span>
            </div>
          )}
          <div className="workbench-top">
            <div
              className="tabs"
              role="tablist"
              aria-label="Investigation views"
            >
              {[
                { id: "investigate", label: "Investigate", icon: Search },
                { id: "history", label: "Time machine", icon: Clock3 },
                {
                  id: "rehearse",
                  label: "Rehearse change",
                  icon: FlaskConical,
                },
              ].map((t) => (
                <button
                  role="tab"
                  aria-selected={tab === t.id}
                  key={t.id}
                  className={tab === t.id ? "selected" : ""}
                  onClick={() => setTab(t.id)}
                >
                  <t.icon size={15} />
                  {t.label}
                </button>
              ))}
            </div>
            <span className="autosave">
              <span className="dot green" />
              Receipts persist in FalkorDB
            </span>
          </div>
          <section className="workbench">
            <div className="change-panel">
              <div className="panel-label">
                <span>01 / PROPOSED CHANGE</span>
                <FileCode2 size={14} />
              </div>
              <h2>Define your change</h2>
              <label className="input-label" htmlFor="question">
                What are you changing?
              </label>
              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={2000}
              />
              <div className="file-chip">
                <FileCode2 size={13} />
                <span>payment_worker.py</span>
                <span>Python</span>
              </div>
              <div className="diff-preview">
                <span className="diff-caption">
                  ILLUSTRATIVE CHANGE · EDIT DELAY BELOW
                </span>
                <code className="deleted">- await sleep(0.250)</code>
                <code className="added">
                  + await sleep({(delay / 1000).toFixed(3)})
                </code>
              </div>
              <div className="form-row">
                <label>
                  Partner scope
                  <select
                    aria-label="Partner scope"
                    value={partner}
                    onChange={(e) => setPartner(e.target.value)}
                  >
                    <option value="all">Both partners</option>
                    <option value="a">Partner A</option>
                    <option value="b">Partner B</option>
                  </select>
                </label>
                <label>
                  Proposed delay
                  <div className="number-field">
                    <input
                      aria-label="Proposed delay in milliseconds"
                      type="number"
                      min={0}
                      max={10000}
                      value={delay}
                      onChange={(e) => setDelay(Number(e.target.value))}
                    />
                    <span>ms</span>
                  </div>
                </label>
              </div>
              <div className="date-fields">
                <label>
                  Effective on
                  <input
                    aria-label="Effective date"
                    type="date"
                    value={effective}
                    onChange={(e) => setEffective(e.target.value)}
                  />
                </label>
                <label>
                  Known by
                  <input
                    aria-label="Knowledge cutoff"
                    type="date"
                    value={known}
                    onChange={(e) => setKnown(e.target.value)}
                  />
                </label>
              </div>
              <label className="gemini-switch">
                <input
                  type="checkbox"
                  checked={gemini}
                  onChange={(e) => setGemini(e.target.checked)}
                  disabled={!health?.gemini_configured}
                />
                <Sparkles size={14} />
                <span>Investigate with Gemini</span>
                <span
                  className={
                    "dot " + (health?.gemini_configured ? "green" : "")
                  }
                />
              </label>
              <button
                className="primary-button investigate-button"
                onClick={investigate}
                disabled={
                  !!busy ||
                  !health?.connected ||
                  question.length < 5 ||
                  !effective ||
                  !known
                }
              >
                {busy === "investigate" ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <Search size={16} />
                )}{" "}
                {busy === "investigate"
                  ? "Following the evidence…"
                  : "Investigate change"}
                {!busy && <ArrowRight size={15} />}
              </button>
              <p className="input-hint">
                Checks the modeled retry requirement.
                <br />
                Arbitrary code analysis is outside this prototype.
              </p>
            </div>
            <div className="graph-panel">
              <div className="graph-heading">
                <div>
                  <span className="panel-label">
                    02 /{" "}
                    {tab === "history"
                      ? "DECISION HISTORY"
                      : tab === "rehearse"
                        ? "CHANGE REHEARSAL"
                        : "EVIDENCE MAP"}
                  </span>
                  <h3>
                    {tab === "history"
                      ? "What applied. What we knew."
                      : tab === "rehearse"
                        ? "Explore the alternative."
                        : "Follow the relationships."}
                  </h3>
                </div>
                <div className="map-heading-actions">
                  <span className="live-tag">
                    <span className="dot green" />
                    FalkorDB
                  </span>
                  {tab !== "history" && (
                    <button
                      className="map-expand"
                      onClick={() => setModal("graph")}
                      aria-label="Expand evidence map"
                      title="Expand evidence map"
                    >
                      <Maximize2 size={15} />
                    </button>
                  )}
                </div>
              </div>
              {tab !== "history" && (
                <div className="map-subbar">
                  <select
                    aria-label="Graph scope"
                    value={graphScope}
                    onChange={(event) => setGraphScope(event.target.value)}
                  >
                    <option value="decision">Decision context</option>
                    <option value="all">All company knowledge</option>
                  </select>
                  <span>
                    {
                      visibleGraph.nodes.filter(
                        (n) =>
                          !["Event", "Team", "Project", "Ticket"].includes(
                            n.kind,
                          ),
                      ).length
                    }{" "}
                    entities · {visibleGraph.edges.length} connections
                  </span>
                </div>
              )}
              {tab === "history" ? (
                <div className="history-view">
                  <div className="context-note">
                    <Clock3 size={18} />
                    <p>
                      <strong>Two clocks. One honest history.</strong>Effective
                      time is when a requirement applied. Knowledge time is when
                      the company learned about it.
                    </p>
                  </div>
                  <div className="preset-row">
                    <button
                      onClick={() => {
                        setEffective("2026-10-11");
                        setKnown("2026-10-11");
                        setPartner("b");
                        setNotice(
                          "Historical dates selected. Run the investigation to see what was known then.",
                        );
                      }}
                    >
                      11 Oct · as known then
                    </button>
                    <button
                      onClick={() => {
                        setEffective("2026-10-11");
                        setKnown("2026-10-15");
                        setPartner("b");
                        setNotice(
                          "Retrospective dates selected. Run the investigation using later knowledge.",
                        );
                      }}
                    >
                      11 Oct · with hindsight
                    </button>
                  </div>
                  <div className="fact-timeline">
                    {facts.map((f) => (
                      <button key={f.id} onClick={() => setSelected(f)}>
                        <span
                          className={
                            "timeline-point " + (f.value === 0 ? "mint" : "")
                          }
                        />
                        <span className="eyebrow">
                          PARTNER {f.partner?.toUpperCase()}
                        </span>
                        <strong>{f.title}</strong>
                        <span>
                          Effective {dateLabel(f.valid_from)} →{" "}
                          {f.valid_to ? dateLabel(f.valid_to) : "ongoing"}
                        </span>
                        <small>
                          Known {dateLabel(f.recorded_from)} →{" "}
                          {f.recorded_to ? dateLabel(f.recorded_to) : "present"}
                        </small>
                      </button>
                    ))}
                  </div>
                  <p className="history-footnote">
                    Replay the migration record below to introduce the
                    late-arriving evidence. Dates are checked at 12:00 UTC.
                  </p>
                </div>
              ) : (
                <>
                  <div className="graph-canvas">
                    <EvidenceGraph
                      graph={visibleGraph}
                      onSelect={setSelected}
                      highlight={selected?.id}
                    />
                    {!graph.nodes.length && (
                      <div className="graph-empty">
                        <Database size={30} />
                        <p>Connect FalkorDB to explore company context.</p>
                      </div>
                    )}
                  </div>
                  <div className="graph-legend">
                    {["System", "Decision", "Source", "Commitment"].map((k) => (
                      <span key={k}>
                        <i style={{ background: KIND_COLORS[k] }} />
                        {k}
                      </span>
                    ))}
                    <span className="graph-legend-hint">
                      Select a node to inspect
                    </span>
                  </div>
                </>
              )}
              {tab === "rehearse" && (
                <div className="rehearsal-box">
                  <div>
                    <FlaskConical size={18} />
                    <span>
                      <strong>Preserve A. Reconsider B.</strong>
                      <small>
                        Copy the graph and check a partner-scoped alternative.
                      </small>
                    </span>
                  </div>
                  <button
                    className="secondary-button"
                    onClick={() =>
                      task("rehearse", async () =>
                        setRehearsal(
                          await api<Rehearsal>("/rehearse", {
                            ...request,
                            partner: "all",
                            use_gemini: false,
                          }),
                        ),
                      )
                    }
                    disabled={!!busy || !health?.connected}
                  >
                    {busy === "rehearse" ? (
                      <LoaderCircle className="spin" size={13} />
                    ) : (
                      <Play size={13} />
                    )}
                    Run rehearsal
                  </button>
                  {rehearsal && (
                    <div className="rehearsal-results">
                      {rehearsal.alternative.map((c) => (
                        <PartnerResult key={c.partner} check={c} />
                      ))}
                      <small>
                        <ShieldCheck size={12} />
                        {rehearsal.base_unchanged
                          ? "Base graph unchanged"
                          : "Base revision changed"}{" "}
                        · {rehearsal.method}
                      </small>
                      <p>{rehearsal.assumptions.join(" ")}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="receipt-panel">
              <div className="panel-label">
                <span>03 / DECISION RECEIPT</span>
                <ShieldCheck size={14} />
              </div>
              {receipt ? (
                <>
                  <div className={"assessment " + receipt.assessment}>
                    {receipt.assessment === "conflict" ? (
                      <ShieldAlert size={24} />
                    ) : receipt.assessment === "no_known_conflict" ? (
                      <ShieldCheck size={24} />
                    ) : (
                      <CircleHelp size={24} />
                    )}
                    <span className="eyebrow">
                      {receipt.mode === "gemini_agent"
                        ? "GEMINI + VERIFIED GRAPH CHECKS"
                        : "VERIFIED GRAPH CHECKS"}
                    </span>
                    <h2>{statusLabel(receipt.assessment)}</h2>
                    <p>
                      {receipt.assessment === "conflict"
                        ? "This change falls below an accepted partner requirement."
                        : receipt.assessment === "no_known_conflict"
                          ? "No conflict in the modeled retry scope. Other risks still require review."
                          : "The graph cannot support a complete assessment."}
                    </p>
                  </div>
                  {(receipt.stale || changed) && (
                    <div className="stale-note">
                      <History size={14} />
                      {receipt.stale
                        ? "Knowledge changed. Rerun this investigation."
                        : "Inputs changed. Run a fresh investigation."}
                    </div>
                  )}
                  <div className="partner-checks">
                    {receipt.checks.map((c) => (
                      <PartnerResult key={c.partner} check={c} />
                    ))}
                  </div>
                  {receipt.agent_error && (
                    <p className="agent-error">{receipt.agent_error}</p>
                  )}
                  {receipt.agent_summary && (
                    <div className="agent-summary">
                      <Sparkles size={14} />
                      <p>{receipt.agent_summary.summary}</p>
                      <small>
                        AI explanation · independently verified checks above
                      </small>
                    </div>
                  )}
                  {receipt.conflicts.length > 0 && (
                    <div className="conflict-card">
                      <span>
                        <BookOpen size={13} />
                        KNOWLEDGE CONFLICT
                      </span>
                      {receipt.conflicts.map((c, i) => (
                        <button
                          key={i}
                          onClick={() =>
                            setSelected(
                              receipt.sources.find(
                                (s) => s.id === c.source_id,
                              ) || null,
                            )
                          }
                        >
                          {c.message}
                          <ArrowUpRight size={12} />
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="receipt-section-title">
                    SUPPORTING EVIDENCE<span>{receipt.sources.length}</span>
                  </div>
                  <div className="evidence-list">
                    {receipt.sources.map((s, i) => (
                      <button key={s.id} onClick={() => setSelected(s)}>
                        <span className="source-number">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <strong>{s.title}</strong>
                          <small>
                            {s.source_type} · {dateLabel(s.timestamp)}
                          </small>
                        </div>
                        <ArrowUpRight size={13} />
                      </button>
                    ))}
                  </div>
                  <button
                    className="secondary-button repair-button"
                    onClick={prepare}
                    disabled={!!busy || receipt.stale || !!changed}
                  >
                    <FileText size={14} />
                    Prepare repair plan
                    <ArrowRight size={14} />
                  </button>
                  <details className="trace-details">
                    <summary>
                      <Terminal size={13} />
                      Tools & measured timings
                      <ChevronDown size={12} />
                    </summary>
                    {receipt.trace.map((t, i) => (
                      <div key={i}>
                        <code>{t.tool}</code>
                        <span>{t.ms} ms</span>
                      </div>
                    ))}
                    <p>
                      Graph checks {receipt.graph_ms} ms · Gemini{" "}
                      {receipt.model_ms} ms · Total {receipt.total_ms} ms
                    </p>
                    <p>
                      Receipt revision {receipt.revision}.{" "}
                      {receipt.gaps.join(" ")}
                    </p>
                  </details>
                </>
              ) : (
                <div className="receipt-empty">
                  <div className="receipt-illustration">
                    <ShieldCheck size={35} />
                    <span />
                    <span />
                    <span />
                  </div>
                  <h3>A conclusion you can inspect.</h3>
                  <p>
                    Run an investigation to reveal applicable decisions,
                    original sources, and the path behind the answer.
                  </p>
                  <span className="small-tag">EVIDENCE BEFORE CONFIDENCE</span>
                </div>
              )}
            </div>
          </section>
          <section className="replay-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">WATCH CONTEXT CHANGE THE ANSWER</span>
                <h3>One company. Evolving knowledge.</h3>
              </div>
              <span className="sample-label">
                Sample event replay <CircleHelp size={13} />
              </span>
            </div>
            <div className="event-grid">
              {events.map((e, i) => (
                <button
                  disabled={!!busy || !health?.connected || eventApplied(e.id)}
                  key={e.id}
                  onClick={() => replay(e.id)}
                >
                  <span className="event-index">0{i + 1}</span>
                  <span className="event-icon">
                    <e.icon size={18} />
                  </span>
                  <span>
                    <strong>{e.title}</strong>
                    <small>
                      {eventApplied(e.id)
                        ? "Applied · persisted in graph"
                        : e.sub}
                    </small>
                  </span>
                  <span className="replay-play">
                    {busy === e.id ? (
                      <LoaderCircle size={15} className="spin" />
                    ) : eventApplied(e.id) ? (
                      <Check size={15} />
                    ) : (
                      <Play size={14} />
                    )}
                  </span>
                </button>
              ))}
            </div>
          </section>
          <footer>
            <span>
              <Network size={13} />
              ChronosGraph <i />
              Company knowledge, with a memory.
            </span>
            <span>
              Fictional company · no external actions published{" "}
              <ArrowUpRight size={12} />
            </span>
          </footer>
        </div>
      </main>
      {selected && (
        <div className="drawer-backdrop" onClick={() => setSelected(null)}>
          <aside className="source-drawer" onClick={(e) => e.stopPropagation()}>
            <button
              className="close-button"
              onClick={() => setSelected(null)}
              aria-label="Close evidence"
            >
              <X size={20} />
            </button>
            <span className="eyebrow">
              {selected.kind.toUpperCase()} / SOURCE INSPECTOR
            </span>
            <h2>{selected.title}</h2>
            <span className="small-tag">{selected.id}</span>
            {selected.excerpt ? (
              <>
                <div className="source-meta">
                  <span>{selected.source_type}</span>
                  <span>{dateLabel(selected.timestamp)}</span>
                </div>
                <blockquote>{selected.excerpt}</blockquote>
                {selected.enabled === false && (
                  <div className="alert error">
                    This evidence has been withdrawn.
                  </div>
                )}
                <p className="input-hint">
                  Fictional source supplied with the NovaPay demo. No live
                  external connection is implied.
                </p>
              </>
            ) : (
              <div className="entity-properties">
                {Object.entries(selected)
                  .filter(([k]) => !["id", "title", "kind"].includes(k))
                  .map(([k, v]) => (
                    <div key={k}>
                      <span>{k.replaceAll("_", " ")}</span>
                      <strong>{String(v) || "Open-ended"}</strong>
                    </div>
                  ))}
              </div>
            )}
            <button
              className="secondary-button"
              onClick={() => {
                navigator.clipboard
                  .writeText(
                    selected.excerpt || JSON.stringify(selected, null, 2),
                  )
                  .then(() => setNotice("Evidence copied."))
                  .catch(() =>
                    setNotice("Clipboard unavailable in this browser."),
                  );
              }}
            >
              <Copy size={14} />
              Copy evidence
            </button>
          </aside>
        </div>
      )}
      {modal && (
        <div className="modal-backdrop" onClick={() => setModal("")}>
          <section
            className={
              "modal " +
              (modal === "repair"
                ? "wide"
                : modal === "graph"
                  ? "map-modal"
                  : "")
            }
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label={
              modal === "repair"
                ? "Repair plan"
                : modal === "receipts"
                  ? "Saved receipts"
                  : modal === "sources"
                    ? "Knowledge sources"
                    : modal === "graph"
                      ? "Expanded evidence map"
                      : "Setup and scope"
            }
          >
            <button
              className="close-button"
              onClick={() => setModal("")}
              aria-label="Close dialog"
            >
              <X size={20} />
            </button>
            {modal === "graph" && (
              <>
                <span className="eyebrow">CONNECTED COMPANY CONTEXT</span>
                <h2>The evidence, in focus.</h2>
                <p className="modal-description">
                  Explore {visibleGraph.nodes.length} entities and their
                  relationships. Select a node to inspect its source.
                </p>
                <div className="expanded-map">
                  <EvidenceGraph
                    graph={visibleGraph}
                    onSelect={(entity) => {
                      setModal("");
                      setSelected(entity);
                    }}
                    highlight={selected?.id}
                  />
                </div>
              </>
            )}
            {modal === "sources" && (
              <>
                <span className="eyebrow">COMPANY KNOWLEDGE</span>
                <h2>Sources with a paper trail.</h2>
                <p className="modal-description">
                  Fictional, versioned evidence stored in FalkorDB.
                </p>
                <div className="modal-list">
                  {sources.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => {
                        setModal("");
                        setSelected(s);
                      }}
                    >
                      <BookOpen size={18} />
                      <span>
                        <strong>{s.title}</strong>
                        <small>
                          {s.source_type} ·{" "}
                          {s.enabled === false ? "Withdrawn" : "Available"}
                        </small>
                      </span>
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              </>
            )}
            {modal === "receipts" && (
              <>
                <span className="eyebrow">PERSISTENT COMPANY MEMORY</span>
                <h2>Decision receipts.</h2>
                <p className="modal-description">
                  Saved in FalkorDB. Reopen an investigation after a refresh.
                </p>
                <div className="modal-list">
                  {history.length ? (
                    history.map((r) => (
                      <button
                        key={r.id}
                        onClick={() => {
                          setReceipt(r);
                          setQuestion(r.request.question as string);
                          setPartner(r.request.partner as string);
                          setDelay(r.request.proposed_ms as number);
                          setEffective(
                            (r.request.effective_at as string).slice(0, 10),
                          );
                          setKnown((r.request.known_at as string).slice(0, 10));
                          setModal("");
                          setTab("investigate");
                        }}
                      >
                        <ShieldCheck size={18} />
                        <span>
                          <strong>{r.title}</strong>
                          <small>
                            {statusLabel(r.assessment)} · revision {r.revision}
                            {r.stale ? " · stale" : ""}
                          </small>
                        </span>
                        <ArrowUpRight size={15} />
                      </button>
                    ))
                  ) : (
                    <p>No receipts yet. Run your first investigation.</p>
                  )}
                </div>
              </>
            )}
            {modal === "repair" && action && (
              <>
                <span className="eyebrow">FROM CONTEXT TO ACTION</span>
                <h2>A repair plan, ready for review.</h2>
                <p className="modal-description">
                  Reviewer: {action.reviewer} ·{" "}
                  {action.status === "approved_in_app"
                    ? "Approved in this workspace"
                    : "Draft prepared"}
                </p>
                <pre className="repair-markdown">{action.markdown}</pre>
                <div className="modal-actions">
                  <button
                    className="secondary-button"
                    onClick={() => {
                      const url = URL.createObjectURL(
                        new Blob([action.markdown], { type: "text/markdown" }),
                      );
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "chronosgraph-repair.md";
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    <FileText size={14} />
                    Download Markdown
                  </button>
                  <button
                    className="primary-button"
                    disabled={!!busy || action.status === "approved_in_app"}
                    onClick={() =>
                      task("approve", async () =>
                        setAction(
                          await api<Action>(
                            `/actions/${action.id}/approve`,
                            {},
                          ),
                        ),
                      )
                    }
                  >
                    <CheckCheck size={14} />
                    {action.status === "approved_in_app"
                      ? "Approved in app"
                      : "Approve in app"}
                  </button>
                </div>
                <p className="input-hint">
                  No GitHub PR, ticket, message, or production change is
                  published.
                </p>
              </>
            )}
            {modal === "setup" && (
              <>
                <span className="eyebrow">LOCAL PROTOTYPE / V0.1</span>
                <h2>Real graph. Explicit boundaries.</h2>
                <div className="setup-row">
                  <Database size={20} />
                  <div>
                    <strong>FalkorDB</strong>
                    <p>
                      {health?.connected
                        ? "Connected · company knowledge and receipts persist locally."
                        : "Unavailable. Run docker compose up -d from the project folder."}
                    </p>
                  </div>
                </div>
                <div className="setup-row">
                  <Sparkles size={20} />
                  <div>
                    <strong>Gemini investigator</strong>
                    <p>
                      {health?.gemini_configured
                        ? `Key configured. Model: ${health.gemini_model}. Enable the checkbox to use the tool loop.`
                        : "Add GEMINI_API_KEY to the project .env file, then restart the API. Never paste keys into the browser."}
                    </p>
                  </div>
                </div>
                <div className="setup-row">
                  <ShieldCheck size={20} />
                  <div>
                    <strong>Supported scope</strong>
                    <p>
                      Payment worker minimum retry delay, Partner A and B, valid
                      and recorded time, documentation conflicts, graph-copy
                      rehearsal, and in-app repair approval.
                    </p>
                  </div>
                </div>
                <div className="setup-row">
                  <CircleHelp size={20} />
                  <div>
                    <strong>Demo data and limitations</strong>
                    <p>
                      NovaPay is fictional. Source ingestion is seeded sample
                      replay. No live app connectors, arbitrary code review,
                      external publishing, production safety guarantees, or
                      enterprise access controls are claimed.
                    </p>
                  </div>
                </div>
                <a
                  className="secondary-button"
                  href="https://www.wemakedevs.org/hackathons/falkordb"
                  target="_blank"
                  rel="noreferrer"
                >
                  Official hackathon requirements
                  <ArrowUpRight size={14} />
                </a>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {import.meta.env.VITE_PUBLIC_EVALUATION !== "1" &&
    new URLSearchParams(window.location.search).get("demo") === "payments" ? (
      <App />
    ) : (
      <CompanyWorkspace />
    )}
  </React.StrictMode>,
);
