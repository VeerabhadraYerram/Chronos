import { useMemo, useState } from "react";
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
  Building2,
  Users,
  FileText,
  Package,
  MapPin,
  GitBranch,
  ShieldCheck,
  ArrowUpRight,
  ArrowRight,
  Network,
  AlignLeft,
} from "lucide-react";
import type { CompanyEntity, CompanyGraph as Graph } from "./company-types";

const palette: Record<string, string> = {
  Client: "#5268b2",
  Rule: "#a66b37",
  Source: "#37816d",
  Team: "#8370a2",
  Facility: "#546e83",
  Decision: "#a66b37",
  Shipment: "#5268b2",
  ScanEvent: "#37816d",
};
const names: Record<string, string> = {
  Client: "CLIENT",
  Rule: "ACCEPTED RULE",
  Claim: "DOCUMENT STATEMENT",
  Source: "EVIDENCE",
  Team: "DEPARTMENT",
  Facility: "FACILITY",
  Decision: "DECISION",
  Policy: "OPERATING POLICY",
  ScanEvent: "TRACKING EVENT",
  ClientWarehouse: "PICKUP LOCATION",
};
const relationNames: Record<string, string> = {
  HAS_COMMITMENT: "has a commitment",
  APPLIES_AT: "applies at",
  SUPPORTED_BY: "supported by",
  OWNED_BY: "owned by",
  WHY: "reason recorded in",
  EXPLAINED_BY: "explained by",
  OPERATED_BY: "operated by",
  AMENDED_BY: "amended by",
  SUPERSEDES: "replaces",
  FOR_CLIENT: "for client",
  AT: "at facility",
  PUBLIC_RELATIONSHIP: "public business relationship",
  DOCUMENTED_IN: "documented in",
  COLLECTED_BY: "collected through",
  ON_MANIFEST: "listed on",
  HAS_SCAN: "tracking event",
  FROM: "collected from",
  USES_ROUTE: "uses route",
  ORIGIN: "starts at",
  DESTINATION: "ends at",
  BELONGS_TO: "belongs to",
};
export const relationLabel = (relation: string) =>
  relationNames[relation] || relation.toLowerCase().replaceAll("_", " ");
function Card({ data }: NodeProps) {
  const entity = data.entity as CompanyEntity;
  const Icon =
    entity.kind === "Client"
      ? Building2
      : entity.kind === "Team"
        ? Users
        : entity.kind === "Source"
          ? FileText
          : entity.kind === "Facility"
            ? MapPin
            : entity.kind === "Rule"
              ? ShieldCheck
              : entity.kind === "Shipment"
                ? Package
                : GitBranch;
  const color = palette[entity.kind] || "#677587";
  return (
    <div
      className={
        "cg-node " +
        (data.selected ? "cg-node-selected" : "") +
        (entity.enabled === false ? " cg-withdrawn" : "")
      }
      style={{ "--cg-color": color } as React.CSSProperties}
      role="button"
      tabIndex={0}
      aria-label={`${names[entity.kind] || entity.kind}: ${entity.title}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          e.currentTarget.click();
        }
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div className="cg-node-top">
        <Icon size={14} />
        <span>{names[entity.kind] || entity.kind.toUpperCase()}</span>
        <ArrowUpRight size={12} />
      </div>
      <strong>{entity.title}</strong>
      <small>
        {entity.enabled === false
          ? "Evidence withdrawn"
          : entity.kind === "Source"
            ? entity.source_type
            : entity.kind === "Rule"
              ? "Click to trace its evidence"
              : entity.kind === "Team"
                ? "Click to explore responsibility"
                : "Click to investigate"}
      </small>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { evidence: Card };
export default function CompanyGraph({
  graph,
  selected,
  onSelect,
  onEdge,
  expanded = false,
}: {
  graph: Graph;
  selected?: string;
  onSelect: (e: CompanyEntity) => void;
  onEdge: (e: Graph["edges"][number]) => void;
  expanded?: boolean;
}) {
  const [map, setMap] = useState(expanded);
  const [showAll, setShowAll] = useState(false);
  const { nodes, edges } = useMemo(() => {
    const tiers: Record<string, number> = {
      Client: 0,
      Company: 0,
      Rule: 1,
      Decision: 1,
      Policy: 1,
      ClientWarehouse: 1,
      Source: 2,
      Facility: 2,
      Campaign: 2,
      Team: 3,
      Shipment: 1,
      ScanEvent: 2,
      PickupRequest: 2,
      Manifest: 2,
      Route: 3,
    };
    const cols = new Map<number, CompanyEntity[]>();
    for (const n of graph.nodes) {
      const c = tiers[n.kind] ?? 2;
      cols.set(c, [...(cols.get(c) || []), n]);
    }
    const nodes = graph.nodes.map((n) => {
      const c = tiers[n.kind] ?? 2;
      const col = cols.get(c)!;
      const row = col.indexOf(n);
      return {
        id: n.id,
        type: "evidence",
        position: { x: c * 300, y: row * 185 - (col.length - 1) * 92.5 },
        data: { entity: n, selected: n.id === selected },
        draggable: true,
      };
    });
    const ids = new Set(nodes.map((n) => n.id));
    const edges = graph.edges
      .filter((e) => ids.has(e.source) && ids.has(e.target))
      .map((e, i) => ({
        id: `${e.source}-${e.relation}-${e.target}-${i}`,
        source: e.source,
        target: e.target,
        label: relationLabel(e.relation),
        data: { edge: e },
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, color: "#a3acae" },
        style: {
          stroke:
            selected && (e.source === selected || e.target === selected)
              ? "#b77b40"
              : "#b5c0be",
          strokeWidth:
            selected && (e.source === selected || e.target === selected)
              ? 2.2
              : 1.5,
        },
        labelStyle: { fontSize: 14, fill: "#46554d" },
        labelBgStyle: { fill: "#fafbf8" },
        labelBgPadding: [6, 4] as [number, number],
      }));
    return { nodes, edges };
  }, [graph, selected]);
  const relationOrder = [
    "HAS_COMMITMENT",
    "SUPPORTED_BY",
    "APPLIES_AT",
    "OWNED_BY",
    "WHY",
    "EXPLAINED_BY",
  ];
  const ordered = [...graph.edges].sort(
    (a, b) =>
      (relationOrder.indexOf(a.relation) < 0
        ? 99
        : relationOrder.indexOf(a.relation)) -
      (relationOrder.indexOf(b.relation) < 0
        ? 99
        : relationOrder.indexOf(b.relation)),
  );
  const sentenceRows = showAll ? ordered : ordered.slice(0, 7);
  const isolated = graph.nodes.filter(
    (n) => !graph.edges.some((e) => e.source === n.id || e.target === n.id),
  );
  const record = (id: string) => graph.nodes.find((n) => n.id === id);
  const nodeButton = (n: CompanyEntity) => (
    <button
      className={"cg-trail-record " + (selected === n.id ? "selected" : "")}
      style={
        { "--cg-color": palette[n.kind] || "#677587" } as React.CSSProperties
      }
      onClick={() => onSelect(n)}
    >
      <small>{names[n.kind] || n.kind.toUpperCase()}</small>
      <strong>{n.title}</strong>
      <ArrowUpRight size={12} />
    </button>
  );
  return (
    <>
      <div className="cg-display-mode">
        <span>
          {map
            ? "Explore the connections spatially."
            : "Read each connection like a sentence."}
        </span>
        <div>
          <button
            className={!map ? "active" : ""}
            onClick={() => setMap(false)}
          >
            <AlignLeft size={12} />
            Readable trail
          </button>
          <button className={map ? "active" : ""} onClick={() => setMap(true)}>
            <Network size={12} />
            Map
          </button>
        </div>
      </div>
      {!map ? (
        <div className="cg-trail">
          {sentenceRows.map((e, i) => {
            const a = record(e.source),
              b = record(e.target);
            return a && b ? (
              <div
                key={e.source + e.relation + e.target + i}
                className="cg-trail-row"
              >
                {nodeButton(a)}
                <button className="cg-trail-relation" onClick={() => onEdge(e)}>
                  <span>{relationLabel(e.relation)}</span>
                  <ArrowRight size={15} />
                </button>
                {nodeButton(b)}
              </div>
            ) : null;
          })}
          {isolated.map((n) => (
            <div key={n.id} className="cg-trail-single">
              {nodeButton(n)}
            </div>
          ))}
          {ordered.length > 7 && (
            <button className="cg-more" onClick={() => setShowAll(!showAll)}>
              {showAll
                ? "Show fewer connections"
                : `Show ${ordered.length - 7} more connections`}
            </button>
          )}
        </div>
      ) : (
        <div className={"cg-canvas " + (expanded ? "cg-canvas-expanded" : "")}>
          <ReactFlow
            key={nodes
              .map((n) => n.id)
              .sort()
              .join(",")}
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodeClick={(_, n) => onSelect(n.data.entity)}
            onEdgeClick={(_, e) => {
              if (e.data?.edge) onEdge(e.data.edge);
            }}
            fitView
            fitViewOptions={{ padding: 0.15, minZoom: 0.45, maxZoom: 0.95 }}
            minZoom={0.15}
            maxZoom={1.5}
            nodesConnectable={false}
            edgesFocusable={true}
            colorMode="light"
          >
            <Background color="#dce2db" gap={22} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
      )}
    </>
  );
}
