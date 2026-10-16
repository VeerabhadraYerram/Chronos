import { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  ArrowLeft,
  BookOpen,
  Check,
  ChevronRight,
  Clock3,
  Download,
  FileText,
  GitBranch,
  History,
  LoaderCircle,
  Maximize2,
  MessageSquare,
  Network,
  Plus,
  Search,
  ShieldAlert,
  Info,
  ShieldCheck,
  Sparkles,
  X,
  Building2,
  Package,
  SlidersHorizontal,
  RotateCcw,
  ExternalLink,
  PanelRightClose,
} from "lucide-react";
import { api } from "./api";
import CompanyGraph, { relationLabel } from "./CompanyGraph";
import type {
  CompanyEntity,
  CompanyGraph as Graph,
  CompanyEdge,
  CompanyReceipt,
  CompanySession,
  Preview,
} from "./company-types";
import "./company.css";
const initialQuestion = "What evidence do we have for this company?";
const emptyGraph: Graph = { nodes: [], edges: [] };
const status = (s: string) =>
  s === "not_assessed"
    ? "Outside modeled scope"
    : s === "conflict"
      ? "Commitment conflict"
      : s === "insufficient_evidence"
        ? "Evidence incomplete"
        : "No modeled conflict";
const day = (s: string) =>
  new Date(s + "T12:00:00Z").toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
export default function CompanyWorkspace() {
  const [session, setSession] = useState<CompanySession | null>(null);
  const [guided, setGuided] = useState(false);
  const [question, setQuestion] = useState("");
  const [effective, setEffective] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [known, setKnown] = useState(new Date().toISOString().slice(0, 10));
  const [client, setClient] = useState("all");
  const [gemini, setGemini] = useState(false);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<CompanyReceipt | null>(null);
  const [trail, setTrail] = useState<CompanyReceipt[]>([]);
  const [selected, setSelected] = useState<CompanyEntity | null>(null);
  const [edge, setEdge] = useState<CompanyEdge | null>(null);
  const [view, setView] = useState<
    "investigate" | "compare" | "records" | "history"
  >("investigate");
  const [expanded, setExpanded] = useState(false);
  const [graph, setGraph] = useState<Graph>(emptyGraph);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [afterMode, setAfterMode] = useState<"proposal" | "alternative">(
    "proposal",
  );
  const [close, setClose] = useState(true);
  const [filters, setFilters] = useState<string[]>([]);
  const [recordQuery, setRecordQuery] = useState("");
  const [records, setRecords] = useState<CompanyEntity[]>([]);
  const [packet, setPacket] = useState<string | null>(null);
  const [help, setHelp] = useState(false);
  const [notice, setNotice] = useState("");
  const initialized = useRef(false);
  const input = useRef<HTMLTextAreaElement>(null);
  const context = {
    effective_at: effective + "T12:00:00Z",
    known_at: known + "T12:00:00Z",
    client,
    use_gemini: gemini,
    close_sunday: close,
  };
  const companyName = session?.company?.title || "Company workspace";
  const clientNames: Record<string, string> = {
    all: "All clients",
    ...Object.fromEntries((session?.clients || []).map((c) => [c.id, c.title])),
  };
  const visibleKinds = [...new Set(graph.nodes.map((n) => n.kind))];
  const starters = guided
    ? (session?.demo?.examples || []).map((s) => ({ ...s, icon: GitBranch }))
    : graph.nodes
        .filter((n) => n.kind !== "Company")
        .slice(0, 3)
        .map((n) => ({
          label: `Explore ${n.title}`,
          question: `What evidence is connected to ${n.title}?`,
          icon: Network,
        }));
  const changed =
    !!receipt &&
    (receipt.request.effective_at !== context.effective_at ||
      receipt.request.known_at !== context.known_at ||
      receipt.request.client !== client);
  async function task(name: string, fn: () => Promise<void>) {
    setBusy(name);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Unable to complete this request.",
      );
    } finally {
      setBusy("");
    }
  }
  async function load(fresh = false) {
    const stored = fresh
      ? null
      : new URLSearchParams(window.location.search).get("workspace") ||
        localStorage.getItem("chronos-company-session");
    const result = await api<CompanySession>("/company/session", {
      session_id: stored,
    });
    localStorage.setItem("chronos-company-session", result.session_id);
    setSession(result);
    setGuided(false);
    setClient("all");
    setGemini(result.investigator_configured);
    setGraph(result.graph);
    setRecords(result.sources);
    setSelected(null);
    setReceipt(null);
    setTrail([]);
    setPreview(null);
    setPacket(null);
    setFilters([]);
  }
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    void task("connect", () => load());
  }, []);
  useEffect(() => {
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (expanded) setExpanded(false);
        else if (help) setHelp(false);
        else if (packet) setPacket(null);
        else {
          setSelected(null);
          setEdge(null);
        }
      }
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, [expanded, help, packet]);
  async function ask(text = question, focus = selected?.id) {
    if (!session || busy || !text.trim()) return;
    setQuestion(text);
    setView("investigate");
    setEdge(null);
    await task("ask", async () => {
      const r = await api<CompanyReceipt>("/company/ask", {
        session_id: session.session_id,
        question: text,
        focus_id: focus || null,
        parent_receipt_id: receipt?.id || null,
        ...context,
      });
      setReceipt(r);
      setClient(r.request.client);
      setGraph(r.graph);
      setFilters([]);
      setTrail((t) => [...t, r]);
      setSelected(null);
      setSession((s) =>
        s
          ? { ...s, receipts: [r, ...s.receipts.filter((x) => x.id !== r.id)] }
          : s,
      );
    });
  }
  function restore(r: CompanyReceipt) {
    setReceipt(r);
    setGraph(r.graph);
    setQuestion(r.title);
    setEffective(r.request.effective_at.slice(0, 10));
    setKnown(r.request.known_at.slice(0, 10));
    setClient(r.request.client);
    setSelected(null);
    setEdge(null);
    setFilters([]);
    setView("investigate");
  }
  async function inspect(entity: CompanyEntity) {
    setExpanded(false);
    setSelected(entity);
    setEdge(null);
  }
  async function expand() {
    if (!session || !selected) return;
    await task("explore", async () => {
      const result = await api<{ graph: Graph }>("/company/explore", {
        session_id: session.session_id,
        id: selected.id,
        depth: 1,
      });
      setGraph(result.graph);
      setFilters([]);
      setNotice(
        "Showing direct connections. This exploration can include historical records; inspect their dates.",
      );
    });
  }
  async function replay(event: "amendment" | "withdraw") {
    if (!session) return;
    await task(event, async () => {
      const result = await api<{ message: string }>("/company/events", {
        session_id: session.session_id,
        event,
      });
      const next = await api<CompanySession>("/company/session", {
        session_id: session.session_id,
      });
      setSession(next);
      setRecords(next.sources);
      setPreview(null);
      setTrail((t) => t.map((r) => ({ ...r, stale: true })));
      if (receipt) setReceipt({ ...receipt, stale: true });
      setNotice(result.message);
    });
  }
  async function runPreview() {
    if (!session) return;
    await task("preview", async () => {
      const result = await api<Preview>("/company/simulate", {
        session_id: session.session_id,
        question: question || initialQuestion,
        ...context,
      });
      setPreview(result);
    });
  }
  const filteredGraph = filters.length
    ? {
        nodes: graph.nodes.filter((n) => filters.includes(n.kind)),
        edges: graph.edges.filter(
          (e) =>
            graph.nodes.some(
              (n) => n.id === e.source && filters.includes(n.kind),
            ) &&
            graph.nodes.some(
              (n) => n.id === e.target && filters.includes(n.kind),
            ),
        ),
      }
    : graph;
  const canAsk = !!session && !busy;
  const evidenceGraph = (
    <CompanyGraph
      graph={filteredGraph}
      selected={selected?.id}
      onSelect={inspect}
      onEdge={(e) => {
        setExpanded(false);
        setEdge(e);
        setSelected(null);
      }}
      expanded={expanded}
    />
  );
  const inspector = selected || edge;
  return (
    <div className="co-app">
      <aside className="co-sidebar">
        <a className="co-brand" href="/">
          <span className="co-brand-icon">
            <Network size={20} />
          </span>
          <span>
            chronos<span className="co-brand-light">graph</span>
            <small>COMPANY MEMORY</small>
          </span>
        </a>
        <button className="co-workspace" onClick={() => setHelp(true)}>
          <span className="co-workspace-mark">{companyName.slice(0, 1)}</span>
          <span>
            {companyName}
            <small>Company workspace</small>
          </span>
          <ChevronRight size={14} />
        </button>
        <div className="co-nav-label">WORKSPACE</div>
        <nav>
          {(
            [
              { id: "investigate", label: "Investigate", icon: MessageSquare },
              {
                id: "compare",
                label: "Demo rehearsal",
                icon: SlidersHorizontal,
              },
              { id: "records", label: "Company records", icon: BookOpen },
              { id: "history", label: "Saved investigations", icon: History },
            ] as const
          )
            .filter((n) => n.id !== "compare" || (guided && !!session?.demo))
            .map((n) => (
              <button
                key={n.id}
                className={view === n.id ? "active" : ""}
                onClick={() => setView(n.id)}
              >
                <n.icon size={17} />
                {n.label}
                {n.id === "history" && !!session?.receipts.length && (
                  <span>{session.receipts.length}</span>
                )}
              </button>
            ))}
        </nav>
        <div className="co-sidebar-story">
          <span className="co-mini-label">COMPANY BRAIN</span>
          <strong>
            {guided ? session?.demo?.title : "Evidence before answers."}
          </strong>
          <p>
            {guided
              ? session?.demo?.description
              : "Explore decisions, ownership and policies across your company records."}
          </p>
          {session?.demo && (
            <button
              onClick={() => {
                setGuided(!guided);
                setView("investigate");
                if (!guided) {
                  setQuestion(session.demo!.question);
                  setEffective(session.demo!.effective_at);
                  setKnown(session.demo!.known_at);
                } else {
                  setClient("all");
                }
              }}
            >
              {guided ? "Leave guided demo" : "Open guided demo"}
              <ArrowUpRight size={13} />
            </button>
          )}
        </div>
        <div className="co-sidebar-bottom">
          <span className={"co-connection " + (session ? "online" : "")}>
            <i />
            {session ? "FalkorDB connected" : "Waiting for FalkorDB"}
          </span>
          <button onClick={() => setHelp(true)}>
            <ShieldCheck size={15} /> About this workspace
          </button>
          <a href="/?demo=payments">
            Original payments prototype <ArrowUpRight size={11} />
          </a>
        </div>
      </aside>
      <main className="co-main">
        <header className="co-topbar">
          <div>
            Workspace <ChevronRight size={12} />
            <strong>{companyName}</strong>
          </div>
          <span className="co-demo-pill">
            {session?.demo ? "SYNTHETIC DATA" : "COMPANY WORKSPACE"}
          </span>
          <button
            title="Create a fresh, separate demo workspace"
            disabled={!!busy}
            onClick={() => void task("connect", () => load(true))}
          >
            <Plus size={14} /> New workspace
          </button>
        </header>
        <div className="co-page">
          <div className="co-page-heading">
            <div>
              <span className="co-eyebrow">CONTEXT BEFORE CONSEQUENCES</span>
              <h1>
                {view === "compare"
                  ? "See the change before you make it."
                  : view === "records"
                    ? "The company, connected."
                    : view === "history"
                      ? "Every question leaves a trail."
                      : "Company answers. Clear evidence."}
              </h1>
              <p>
                {view === "compare"
                  ? "Compare processing rules, affected consignments and commitments in an isolated graph copy."
                  : view === "records"
                    ? "Inspect the records behind the answer. Public references and synthetic evidence are distinguished."
                    : view === "history"
                      ? "Reopen the evidence and context behind a previous investigation."
                      : "Ask about decisions, policies or incidents. Follow the records behind the answer, then ask a deeper question."}
              </p>
            </div>
            {session?.demo && (
              <button
                className="co-secondary"
                onClick={() => {
                  setGuided(!guided);
                  setView("investigate");
                  if (!guided) {
                    setQuestion(session.demo!.question);
                    setEffective(session.demo!.effective_at);
                    setKnown(session.demo!.known_at);
                  } else {
                    setClient("all");
                  }
                }}
              >
                {guided ? "Leave demo" : "Guided demo"}
              </button>
            )}
            <button
              className="co-icon-button"
              aria-label="Explain the prototype"
              onClick={() => setHelp(true)}
            >
              <BookOpen size={18} />
            </button>
          </div>
          <div className="co-contextbar">
            <span>
              <Clock3 size={14} />
              Decision context
            </span>
            <label>
              Effective on
              <input
                aria-label="Effective on"
                type="date"
                value={effective}
                onChange={(e) => {
                  setEffective(e.target.value);
                  setPreview(null);
                }}
              />
            </label>
            <label>
              Known by
              <input
                aria-label="Known by"
                type="date"
                value={known}
                onChange={(e) => {
                  setKnown(e.target.value);
                  setPreview(null);
                }}
              />
            </label>
            {guided && session?.demo && (
              <>
                <label>
                  Client
                  <select
                    aria-label="Client scope"
                    value={client}
                    onChange={(e) => {
                      setClient(e.target.value);
                      setPreview(null);
                    }}
                  >
                    {Object.entries(clientNames).map(([id, name]) => (
                      <option key={id} value={id}>
                        {name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  onClick={() => {
                    setEffective(session?.demo?.before_effective || effective);
                    setKnown(session?.demo?.before_known || known);
                    setPreview(null);
                  }}
                >
                  As known then
                </button>
                <button
                  onClick={() => {
                    setEffective(session?.demo?.effective_at || effective);
                    setKnown(session?.demo?.known_at || known);
                    setPreview(null);
                  }}
                >
                  Later knowledge
                </button>
              </>
            )}
          </div>
          {error && (
            <div role="alert" className="co-error">
              <ShieldAlert size={18} />
              <span>
                {error}
                {!session &&
                  " Start Docker and the API, then reconnect. If a saved workspace is missing, create a new one."}
              </span>
              <button onClick={() => void task("connect", () => load())}>
                Reconnect
              </button>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={15} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="co-notice">
              <Check size={16} />
              <span>{notice}</span>
              <button aria-label="Dismiss notice" onClick={() => setNotice("")}>
                <X size={14} />
              </button>
            </div>
          )}
          {view === "investigate" && (
            <>
              <section className="co-query-card">
                <div className="co-query-label">
                  <Sparkles size={15} />
                  <span>ASK YOUR COMPANY MEMORY</span>
                  {selected && (
                    <button onClick={() => setSelected(null)}>
                      About {selected.title}
                      <X size={12} />
                    </button>
                  )}
                </div>
                <textarea
                  ref={input}
                  aria-label="Ask ChronosGraph"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={initialQuestion}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void ask();
                    }
                  }}
                />
                <div className="co-query-bottom">
                  <span>
                    <kbd>↵</kbd> Ask a question · click a graph item to follow
                    up
                  </span>
                  <label>
                    <input
                      type="checkbox"
                      checked={gemini}
                      disabled={!session?.investigator_configured || !!busy}
                      onChange={(e) => setGemini(e.target.checked)}
                    />
                    AI investigator
                  </label>
                  <button
                    className="co-primary"
                    disabled={!canAsk || !question.trim()}
                    onClick={() => void ask()}
                  >
                    {busy === "ask" ? (
                      <LoaderCircle className="co-spin" size={16} />
                    ) : (
                      <ArrowRight size={16} />
                    )}
                    Investigate
                  </button>
                </div>
              </section>
              {!receipt && (
                <div className="co-starters">
                  {starters.map((s) => (
                    <button
                      key={s.label}
                      disabled={!canAsk}
                      onClick={() => void ask(s.question, undefined)}
                    >
                      <s.icon size={15} />
                      {s.label}
                      <ArrowUpRight size={13} />
                    </button>
                  ))}
                </div>
              )}
              {trail.length > 1 && (
                <div className="co-breadcrumbs">
                  <button
                    onClick={() => {
                      const t = trail.slice(0, -1);
                      setTrail(t);
                      restore(t[t.length - 1]);
                    }}
                  >
                    <ArrowLeft size={13} />
                    Back
                  </button>
                  {trail.slice(-3).map((r, i) => (
                    <span key={r.id}>
                      <ChevronRight size={12} />
                      <button onClick={() => restore(r)}>
                        {i === trail.slice(-3).length - 1
                          ? "Current question"
                          : r.title.length > 36
                            ? r.title.slice(0, 36) + "…"
                            : r.title}
                      </button>
                    </span>
                  ))}
                </div>
              )}
              {receipt ? (
                <section className="co-answer">
                  <div className="co-answer-top">
                    <div
                      className="co-alerts"
                      aria-label="Investigation alerts"
                      aria-live="polite"
                    >
                      {receipt.stale || changed ? (
                        <span className="co-status co-alert warning">
                          <Clock3 size={17} />
                          Context needs refresh
                        </span>
                      ) : (
                        receipt.alerts?.map((alert, alertIndex) => (
                          <details
                            className={"co-alert-detail " + alert.severity}
                            key={alert.category + alertIndex}
                          >
                            <summary
                              className={"co-status co-alert " + alert.severity}
                            >
                              {alert.severity === "warning" ? (
                                <ShieldAlert size={17} />
                              ) : alert.severity === "success" ? (
                                <ShieldCheck size={17} />
                              ) : (
                                <Info size={17} />
                              )}
                              {alert.title}
                              <ChevronRight size={14} />
                            </summary>
                            <p>{alert.message}</p>
                          </details>
                        ))
                      )}
                    </div>
                    <span>
                      {receipt.mode === "gemini_agent" ||
                      receipt.mode === "groq_agent" ||
                      receipt.mode === "openrouter_agent"
                        ? `${receipt.provider === "groq" ? "Groq" : receipt.provider === "openrouter" ? "OpenRouter (free)" : "Gemini"} + graph evidence`
                        : receipt.mode === "ai_unavailable"
                          ? "AI answer unavailable"
                          : "Graph-only retrieval"}{" "}
                      · revision {receipt.revision}
                    </span>
                  </div>
                  <div className="co-answer-heading">
                    <span className="co-eyebrow">
                      {receipt.mode === "ai_unavailable"
                        ? "INVESTIGATION STATUS"
                        : "YOUR ANSWER"}
                    </span>
                    <h2>{receipt.title}</h2>
                  </div>
                  <div className="co-answer-copy">
                    {receipt.summary.split(/\n\s*\n/).map((paragraph, i) => (
                      <p key={i} className={i === 0 ? "co-answer-lead" : ""}>
                        {paragraph}
                      </p>
                    ))}
                  </div>
                  <details className="co-source-disclosure">
                    <summary>
                      Sources behind this answer{" "}
                      <span>· open to inspect original evidence</span>
                    </summary>
                    <div className="co-answer-sources">
                      {(receipt.citations?.length
                        ? receipt.sources.filter((s) =>
                            receipt.citations!.includes(s.id),
                          )
                        : receipt.sources.filter((s) =>
                            receipt.graph.nodes.some((n) => n.id === s.id),
                          )
                      ).map((source, i) => (
                        <button
                          key={source.id}
                          onClick={() => {
                            setSelected(source);
                            setEdge(null);
                          }}
                        >
                          <FileText size={12} />
                          <span>
                            {i + 1}. {source.title}
                          </span>
                          <ArrowUpRight size={11} />
                        </button>
                      ))}
                    </div>
                  </details>
                  {!receipt.stale &&
                    !changed &&
                    !!receipt.documents_to_review?.length && (
                      <div className="co-doc-review">
                        <Clock3 size={16} />
                        <div>
                          <strong>One operating document needs review</strong>
                          {receipt.documents_to_review.map((d) => (
                            <button
                              key={d.id}
                              onClick={() => {
                                const source = session?.sources.find(
                                  (s) => s.id === d.source_id,
                                );
                                if (source) setSelected(source);
                              }}
                            >
                              {d.title}: {d.reason}
                              <ArrowUpRight size={12} />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  {(receipt.stale || changed) && (
                    <div className="co-stale">
                      <Clock3 size={14} />
                      {receipt.stale
                        ? "Knowledge changed. Rerun this investigation before using its conclusion."
                        : "The dates or client changed. Rerun to update this answer."}
                      <button
                        disabled={!!busy}
                        onClick={() =>
                          void ask(receipt.title, receipt.request.focus_id)
                        }
                      >
                        Rerun
                      </button>
                    </div>
                  )}
                </section>
              ) : (
                <section className="co-intro">
                  <div className="co-intro-symbol">
                    <GitBranch size={25} />
                  </div>
                  <div>
                    <span className="co-eyebrow">
                      START WITH ONE SIMPLE QUESTION
                    </span>
                    <h2>Ask a question. Follow the evidence.</h2>
                    <p>
                      Explore the records available in this workspace. Inspect
                      sources, discover owners and investigate the policies that
                      apply to your question. Your evidence graph appears after
                      you ask; click any record to investigate further.
                    </p>
                  </div>
                  <span className="co-intro-number">01</span>
                </section>
              )}
              {receipt && (
                <section className="co-evidence">
                  <div className="co-section-heading">
                    <div>
                      <span className="co-eyebrow">
                        THE EVIDENCE, IN PLAIN SIGHT
                      </span>
                      <h2>
                        {receipt
                          ? "Follow the answer back to its source."
                          : "Records. Sources. The connections between them."}
                      </h2>
                    </div>
                    <button
                      className="co-secondary"
                      onClick={() => setExpanded(true)}
                    >
                      <Maximize2 size={14} />
                      Expand
                    </button>
                  </div>
                  <div className="co-graph-toolbar">
                    <span>
                      <i /> {graph.nodes.length} records · {graph.edges.length}{" "}
                      connections
                    </span>
                    <div>
                      {visibleKinds
                        .filter((k) => graph.nodes.some((n) => n.kind === k))
                        .map((k) => (
                          <button
                            className={filters.includes(k) ? "active" : ""}
                            key={k}
                            onClick={() =>
                              setFilters((f) =>
                                f.includes(k)
                                  ? f.filter((x) => x !== k)
                                  : [...f, k],
                              )
                            }
                          >
                            {k === "Rule"
                              ? "Commitments"
                              : k === "Source"
                                ? "Evidence"
                                : k === "Team"
                                  ? "People & teams"
                                  : k === "Facility"
                                    ? "Facilities"
                                    : k === "Company"
                                      ? "Companies"
                                      : k + "s"}
                          </button>
                        ))}
                      {!!filters.length && (
                        <button onClick={() => setFilters([])}>Show all</button>
                      )}
                    </div>
                  </div>
                  {session ? (
                    graph.nodes.length ? (
                      evidenceGraph
                    ) : (
                      <p className="co-empty-proof">
                        No supporting records were selected for this answer. The
                        graph stays empty rather than implying evidence that was
                        not found.
                      </p>
                    )
                  ) : (
                    <div className="co-loading">
                      <LoaderCircle className="co-spin" size={22} />
                      {busy === "connect"
                        ? "Connecting to FalkorDB…"
                        : "Connect the database to explore evidence."}
                    </div>
                  )}
                  <div className="co-graph-caption">
                    <span>
                      <span className="co-number">1</span>Read the labels
                    </span>
                    <span>
                      <span className="co-number">2</span>Click a record or
                      connection
                    </span>
                    <span>
                      <span className="co-number">3</span>Ask a deeper question
                    </span>
                    <button
                      onClick={() => {
                        if (receipt) setGraph(receipt.graph);
                        else if (session) setGraph(session.graph);
                        setFilters([]);
                        setSelected(null);
                        setEdge(null);
                      }}
                    >
                      <RotateCcw size={12} />
                      Reset view
                    </button>
                  </div>
                </section>
              )}
              {receipt && (
                <div className="co-followups">
                  <span>KEEP EXPLORING</span>
                  {receipt.followups.map((q) => (
                    <button
                      key={q}
                      disabled={!!busy}
                      onClick={() => void ask(q, undefined)}
                    >
                      {q}
                      <ArrowUpRight size={13} />
                    </button>
                  ))}
                </div>
              )}
              <div className="co-bottom-grid">
                {guided && session?.demo && (
                  <section className="co-story-card">
                    <span className="co-eyebrow">
                      GUIDED DEMO · SYNTHETIC REPLAY
                    </span>
                    <h3>{session.demo.title}</h3>
                    {session.demo.events.map((event) => (
                      <div key={event.id}>
                        <p>{event.description}</p>
                        <button
                          className="co-secondary"
                          disabled={
                            !!busy ||
                            (event.id === "amendment" &&
                              session.amendment_loaded)
                          }
                          onClick={() => void replay(event.id)}
                        >
                          {event.label}
                          <ArrowUpRight size={13} />
                        </button>
                      </div>
                    ))}
                  </section>
                )}
                {/* The guided fixture is separate from company-wide investigation. */}
                {receipt && receipt.mode !== "ai_unavailable" && (
                  <section className="co-story-card co-story-dark">
                    <span className="co-eyebrow">FROM ANSWER TO REVIEW</span>
                    <h3>
                      Understand the change.
                      <br />
                      Then prepare the work.
                    </h3>
                    <p>
                      Assemble a review packet from the current investigation
                      and its retrieved sources. Every real-world action stays
                      with a human.
                    </p>
                    <div>
                      {guided && session?.demo && (
                        <button
                          className="co-secondary"
                          onClick={() => setView("compare")}
                        >
                          Compare demo scenario <ArrowRight size={14} />
                        </button>
                      )}
                      <button
                        className="co-text-button"
                        disabled={
                          !receipt || !!busy || receipt.stale || changed
                        }
                        onClick={() =>
                          void task("packet", async () => {
                            const r = await api<{ markdown: string }>(
                              "/company/packet",
                              {
                                session_id: session!.session_id,
                                receipt_id: receipt!.id,
                              },
                            );
                            setPacket(r.markdown);
                          })
                        }
                      >
                        Prepare review packet <ArrowUpRight size={13} />
                      </button>
                    </div>
                  </section>
                )}
              </div>
              {receipt && (
                <details className="co-trace">
                  <summary>
                    Inspect retrieval trace ·{" "}
                    {receipt.total_ms.toLocaleString()} ms total
                  </summary>
                  <div>
                    {receipt.trace.map((t, i) => (
                      <p key={i}>
                        <code>{t.tool}</code>
                        <span>
                          {t.rows} rows
                          {t.ms !== undefined ? ` · ${t.ms} ms` : ""}
                        </span>
                      </p>
                    ))}
                  </div>
                </details>
              )}
            </>
          )}
          {view === "compare" && (
            <>
              <section className="co-comparison-intro">
                <div>
                  <span className="co-eyebrow">A REVERSIBLE REHEARSAL</span>
                  <h2>Close Sunday processing?</h2>
                  <p>
                    A temporary copy of the real FalkorDB workspace checks the
                    proposal. Your base knowledge stays untouched. This preview
                    covers all three clients.
                  </p>
                </div>
                <label>
                  <input
                    type="checkbox"
                    checked={close}
                    onChange={(e) => {
                      setClose(e.target.checked);
                      setPreview(null);
                    }}
                  />
                  Close Sundays
                </label>
                <button
                  className="co-primary"
                  disabled={!session || !!busy}
                  onClick={() => void runPreview()}
                >
                  {busy === "preview" ? (
                    <LoaderCircle className="co-spin" size={15} />
                  ) : (
                    <SlidersHorizontal size={15} />
                  )}
                  Run comparison
                </button>
              </section>
              {preview ? (
                <>
                  <div className="co-comparison-top">
                    <span className={"co-status " + preview.assessment}>
                      {status(preview.assessment)}
                    </span>
                    <span>Scenario Sunday: {day(preview.scenario_sunday)}</span>
                    <div className="co-segment">
                      <button
                        className={afterMode === "proposal" ? "active" : ""}
                        onClick={() => setAfterMode("proposal")}
                      >
                        Full proposal
                      </button>
                      <button
                        className={afterMode === "alternative" ? "active" : ""}
                        onClick={() => setAfterMode("alternative")}
                      >
                        Preserve commitments
                      </button>
                    </div>
                  </div>
                  <section className="co-comparison-table">
                    <div className="co-table-head">
                      <span>CLIENT / SUNDAY SAMPLE</span>
                      <strong>
                        Before<small>Current demo handbook</small>
                      </strong>
                      <strong>
                        {afterMode === "proposal"
                          ? "After full closure"
                          : "After scoped alternative"}
                        <small>
                          {afterMode === "proposal"
                            ? "All clients queue for Monday"
                            : "Keep required Sunday exceptions"}
                        </small>
                      </strong>
                      <span>COMMITMENT CHECK</span>
                    </div>
                    {preview.rows.map((r) => (
                      <div className="co-table-row" key={r.client}>
                        <span>
                          <strong>{r.title}</strong>
                          <small>
                            {r.consignments.toLocaleString()} demo consignments
                          </small>
                        </span>
                        <span>
                          {r.before}
                          <small>
                            {r.queued_before.toLocaleString()} queued for Monday
                          </small>
                        </span>
                        <span
                          className={
                            r.before !==
                            (afterMode === "proposal" ? r.after : r.alternative)
                              ? "co-diff"
                              : ""
                          }
                        >
                          {afterMode === "proposal" ? r.after : r.alternative}
                          <small>
                            {(afterMode === "proposal"
                              ? r.queued_after
                              : r.queued_alternative
                            )?.toLocaleString() ?? "Unknown"}{" "}
                            queued for Monday
                          </small>
                        </span>
                        <span
                          className={
                            "co-status " +
                            (r.sunday_required === null
                              ? "insufficient_evidence"
                              : afterMode === "alternative"
                                ? "no_known_conflict"
                                : r.status)
                          }
                        >
                          {r.sunday_required === null
                            ? "Review evidence"
                            : afterMode === "proposal"
                              ? status(r.status)
                              : "Requirement preserved"}
                        </span>
                      </div>
                    ))}
                  </section>
                  <div className="co-preview-metrics">
                    <div>
                      <span>Synthetic shift-cost assumption</span>
                      <strong>
                        ₹{preview.cost.before_inr.toLocaleString()}{" "}
                        <ArrowRight size={17} />{" "}
                        {(afterMode === "proposal"
                          ? preview.cost.proposed_inr
                          : preview.cost.alternative_inr) === null
                          ? "Unknown"
                          : `₹${(afterMode === "proposal" ? preview.cost.proposed_inr : preview.cost.alternative_inr)!.toLocaleString()}`}
                      </strong>
                      <small>Per Sunday shift · not measured savings</small>
                    </div>
                    <div>
                      <span>Base graph</span>
                      <strong>
                        <ShieldCheck size={20} />
                        {preview.base_unchanged
                          ? "Unchanged"
                          : "Revision changed"}
                      </strong>
                      <small>Rehearsal graph removed after comparison</small>
                    </div>
                    <div>
                      <span>Next work to review</span>
                      <strong>Calendar + handbook</strong>
                      <small>Operations · Account Management · Transport</small>
                    </div>
                  </div>
                  <section className="co-assumptions">
                    <h3>What this comparison means</h3>
                    {preview.assumptions.map((a) => (
                      <p key={a}>
                        <Check size={14} />
                        {a}
                      </p>
                    ))}
                    <button
                      className="co-secondary"
                      onClick={() => {
                        setView("investigate");
                        void ask(
                          "Who needs to review the Sunday closure and update the handbook?",
                          undefined,
                        );
                      }}
                    >
                      Investigate the next steps
                      <ArrowRight size={14} />
                    </button>
                  </section>
                </>
              ) : (
                <div className="co-preview-empty">
                  <SlidersHorizontal size={35} />
                  <h2>See the consequences side by side.</h2>
                  <p>
                    Run the comparison to inspect all 1,200 sample consignments,
                    processing changes and supported commitments.
                  </p>
                </div>
              )}
            </>
          )}
          {view === "records" && (
            <>
              <div className="co-data-stats">
                {session &&
                  [
                    ["Graph records", session.stats.entities],
                    ["Relationships", session.stats.connections],
                    ["Sample consignments", session.stats.labels.Shipment || 0],
                    ["Tracking events", session.stats.labels.ScanEvent || 0],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <strong>{Number(value).toLocaleString()}</strong>
                    </div>
                  ))}
              </div>
              <form
                className="co-record-search"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (session)
                    void task("search", async () => {
                      const r = await api<{ records: CompanyEntity[] }>(
                        "/company/search",
                        {
                          session_id: session.session_id,
                          question: recordQuery,
                          ...context,
                        },
                      );
                      setRecords(r.records);
                    });
                }}
              >
                <Search size={17} />
                <input
                  aria-label="Search company records"
                  placeholder="Search agreements, Finance, DEMO-AWB-000001…"
                  value={recordQuery}
                  onChange={(e) => setRecordQuery(e.target.value)}
                />
                <button
                  className="co-secondary"
                  disabled={!recordQuery.trim() || !!busy}
                >
                  Search
                </button>
                <button
                  type="button"
                  className="co-text-button"
                  onClick={() => setRecords(session?.sources || [])}
                >
                  All sources
                </button>
              </form>
              <div className="co-records">
                {records.map((r) => (
                  <button
                    className="co-record"
                    key={r.id}
                    onClick={() => {
                      setSelected(r);
                      setEdge(null);
                    }}
                  >
                    <span className="co-record-icon">
                      <FileText size={18} />
                    </span>
                    <span>
                      <small>
                        {r.classification === "public_reference"
                          ? "PUBLIC REFERENCE"
                          : r.source_type || r.kind.toUpperCase()}
                        {r.enabled === false ? " · WITHDRAWN" : ""}
                      </small>
                      <strong>{r.title}</strong>
                      <p>{r.excerpt || r.description || r.id}</p>
                    </span>
                    <ArrowUpRight size={16} />
                  </button>
                ))}
              </div>
              {!records.length && (
                <p className="co-empty-text">
                  No matching records. Try a company name or a specific record
                  ID.
                </p>
              )}
              <details className="co-schema">
                <summary>
                  Explore the reference schema ·{" "}
                  {session ? Object.keys(session.stats.labels).length : 0}{" "}
                  entity types
                </summary>
                <div>
                  {session &&
                    Object.entries(session.stats.labels).map(
                      ([kind, count]) => (
                        <span key={kind}>
                          {kind}
                          <strong>{count.toLocaleString()}</strong>
                        </span>
                      ),
                    )}
                </div>
                <p>
                  Independently designed graph schema informed by public company
                  evidence. This is an independently designed database schema.
                </p>
              </details>
            </>
          )}
          {view === "history" && (
            <div className="co-history">
              {session?.receipts.length ? (
                session.receipts.map((r) => (
                  <button key={r.id} onClick={() => restore(r)}>
                    <span
                      className={
                        "co-status co-alert " +
                        (r.stale
                          ? "warning"
                          : r.alerts?.[0]?.severity || "info")
                      }
                    >
                      {r.stale
                        ? "Outdated context"
                        : r.alerts?.[0]?.title || "Saved investigation"}
                    </span>
                    <h3>{r.title}</h3>
                    <p>{r.summary}</p>
                    <small>
                      Effective {day(r.request.effective_at.slice(0, 10))} ·
                      known by {day(r.request.known_at.slice(0, 10))} · revision{" "}
                      {r.revision}
                    </small>
                    <ArrowUpRight size={16} />
                  </button>
                ))
              ) : (
                <div className="co-preview-empty">
                  <History size={35} />
                  <h2>Your investigation history starts here.</h2>
                  <p>
                    Ask a question to save an evidence-backed receipt in
                    FalkorDB.
                  </p>
                  <button
                    className="co-secondary"
                    onClick={() => setView("investigate")}
                  >
                    Ask your first question
                    <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </div>
          )}
          <footer className="co-footer">
            <span>
              <Network size={14} />
              ChronosGraph · connected company memory
            </span>
            <span>
              {session?.demo
                ? "Public names. Synthetic private records."
                : "Answers grounded in stored company evidence."}
            </span>
          </footer>
        </div>
      </main>
      {inspector && (
        <aside className="co-inspector">
          <div className="co-inspector-top">
            <span>
              {edge ? "RELATIONSHIP EVIDENCE" : "EXPLORE THIS RECORD"}
            </span>
            <button
              aria-label="Close record inspector"
              onClick={() => {
                setSelected(null);
                setEdge(null);
              }}
            >
              <PanelRightClose size={18} />
            </button>
          </div>
          {selected ? (
            <>
              <span className="co-eyebrow">
                {selected.kind === "Rule"
                  ? "COMMITMENT"
                  : selected.kind.toUpperCase()}
              </span>
              <h2>{selected.title}</h2>
              {selected.enabled === false && (
                <div className="co-stale">
                  This evidence has been withdrawn.
                </div>
              )}
              <span className="co-inspector-classification">
                {selected.classification === "public_reference"
                  ? "Public reference · business context only"
                  : "Synthetic demo record"}
              </span>
              {selected.excerpt ? (
                <blockquote>{selected.excerpt}</blockquote>
              ) : (
                <p>
                  {selected.description ||
                    "Explore this record’s connections and source evidence."}
                </p>
              )}
              <dl>
                {Object.entries(selected)
                  .filter(
                    ([k, v]) =>
                      [
                        "department",
                        "timestamp",
                        "valid_from",
                        "valid_to",
                        "recorded_from",
                        "recorded_to",
                        "client",
                        "status",
                        "arrival_at",
                        "city",
                        "event_at",
                      ].includes(k) && v,
                  )
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt>{k.replaceAll("_", " ")}</dt>
                      <dd>
                        {String(v).replace("T", " ").replace("Z", " UTC")}
                      </dd>
                    </div>
                  ))}
              </dl>
              {selected.url && (
                <a
                  className="co-external"
                  href={selected.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open official reference
                  <ExternalLink size={13} />
                </a>
              )}
              <div className="co-inspector-actions">
                <button
                  className="co-primary"
                  disabled={!!busy}
                  onClick={() => {
                    setQuestion(`Tell me more about ${selected.title}.`);
                    setView("investigate");
                    input.current?.focus();
                  }}
                >
                  Ask about this
                  <MessageSquare size={14} />
                </button>
                <button
                  className="co-secondary"
                  disabled={!!busy}
                  onClick={() => void expand()}
                >
                  Explore connections
                  <Network size={14} />
                </button>
              </div>
              <div className="co-inspector-suggestions">
                <span className="co-eyebrow">FOLLOW THE QUESTION</span>
                {[
                  "Why does this exist?",
                  "Does this still apply?",
                  "Who is responsible for this?",
                ].map((q) => (
                  <button
                    key={q}
                    disabled={!!busy}
                    onClick={() =>
                      void ask(
                        `${q} Selected record: ${selected.title}.`,
                        selected.id,
                      )
                    }
                  >
                    {q}
                    <ArrowUpRight size={13} />
                  </button>
                ))}
              </div>
              <code className="co-record-id">{selected.id}</code>
            </>
          ) : (
            edge && (
              <>
                <span className="co-eyebrow">A CONNECTION YOU CAN CHECK</span>
                <h2>{relationLabel(edge.relation)}</h2>
                <p>
                  <strong>
                    {graph.nodes.find((n) => n.id === edge.source)?.title ||
                      edge.source}
                  </strong>
                  <br />
                  {relationLabel(edge.relation)}
                  <br />
                  <strong>
                    {graph.nodes.find((n) => n.id === edge.target)?.title ||
                      edge.target}
                  </strong>
                </p>
                <h3>Supporting records</h3>
                {edge.source_ids.length ? (
                  edge.source_ids.map((id) => (
                    <button
                      className="co-edge-source"
                      key={id}
                      onClick={() => {
                        const n =
                          session?.sources.find((s) => s.id === id) ||
                          graph.nodes.find((n) => n.id === id);
                        if (n) {
                          setSelected(n);
                          setEdge(null);
                        }
                      }}
                    >
                      <FileText size={15} />
                      {session?.sources.find((s) => s.id === id)?.title || id}
                      <ArrowUpRight size={13} />
                    </button>
                  ))
                ) : (
                  <p>
                    This is a synthetic operational linkage. No document-level
                    provenance is attached to this relationship.
                  </p>
                )}
              </>
            )
          )}
        </aside>
      )}
      {expanded && (
        <div className="co-modal-backdrop" onClick={() => setExpanded(false)}>
          <div
            className="co-graph-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Expanded evidence graph"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="co-section-heading">
              <div>
                <span className="co-eyebrow">FOLLOW THE EVIDENCE</span>
                <h2>Your answer, connected.</h2>
              </div>
              <button
                className="co-icon-button"
                aria-label="Close expanded graph"
                onClick={() => setExpanded(false)}
              >
                <X size={20} />
              </button>
            </div>
            {evidenceGraph}
            <p>
              Click a record to inspect it. Use the inspector to ask a deeper
              question.
            </p>
          </div>
        </div>
      )}
      {help && (
        <div className="co-modal-backdrop" onClick={() => setHelp(false)}>
          <div
            className="co-help-modal"
            role="dialog"
            aria-modal="true"
            aria-label="About this workspace"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="co-modal-close"
              aria-label="Close workspace information"
              onClick={() => setHelp(false)}
            >
              <X size={20} />
            </button>
            <span className="co-eyebrow">WORKSPACE & EVIDENCE</span>
            <h2>{companyName}</h2>
            <p>{session?.disclosure}</p>
            <p>
              Ask a company question, inspect the connected sources and records,
              and follow up on a selected item. Answers are limited by the
              evidence in this workspace.
            </p>
            <p>
              <strong>Workspace ID:</strong> <code>{session?.session_id}</code>
            </p>
            <p>
              This identifier can be entered in the separate database inspection
              portal. It grants access to this synthetic workspace; it is not
              production authentication.
            </p>
            <p>
              <strong>Two clocks:</strong> “Effective on” selects when a
              commitment applies. “Known by” limits what was recorded by then.
              Ownership and topology are current demo relationships.
            </p>
            <p>
              <strong>Mode:</strong> Groq, Gemini or OpenRouter investigates
              when enabled and successful; graph search is explicitly labeled
              otherwise. Sources and retrieval traces remain inspectable.
            </p>
            <p>
              Your workspace has its own graph. New workspace creates a fresh
              copy without erasing the previous one. Session access is intended
              for synthetic demos, not private production data.
            </p>
            <a
              className="co-external"
              href="https://www.delhivery.com/services/express-parcel"
              target="_blank"
              rel="noreferrer"
            >
              Official business reference
              <ExternalLink size={13} />
            </a>
          </div>
        </div>
      )}
      {packet && (
        <div className="co-modal-backdrop" onClick={() => setPacket(null)}>
          <div
            className="co-help-modal co-packet"
            role="dialog"
            aria-modal="true"
            aria-label="Review packet"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="co-modal-close"
              aria-label="Close review packet"
              onClick={() => setPacket(null)}
            >
              <X size={20} />
            </button>
            <span className="co-eyebrow">PREPARED FOR HUMAN REVIEW</span>
            <h2>Company evidence review packet.</h2>
            <p>
              A source-linked local draft. No external ticket, email or schedule
              change has been made.
            </p>
            <pre>{packet}</pre>
            <button
              className="co-primary"
              onClick={() => {
                const url = URL.createObjectURL(
                  new Blob([packet], { type: "text/markdown" }),
                );
                const a = document.createElement("a");
                a.href = url;
                a.download = "chronosgraph-review-packet.md";
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <Download size={15} />
              Download Markdown
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
