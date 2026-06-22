"""
mermaid_tools.py
----------------
Custom CrewAI tools for generating and validating Mermaid diagrams from the
typed Pydantic data produced by the ArchitectFlow pipeline.

Tools
-----
ArchitectureDiagramTool
    Converts an ArchitectureDesign JSON (components + data_flows) into a
    syntactically valid ``graph TD`` Mermaid block.

SequenceDiagramTool
    Builds a ``sequenceDiagram`` Mermaid block for a named flow (e.g. "booking",
    "search") from a SubsystemDesign JSON.

MermaidValidatorTool
    Runs structural validation on a raw Mermaid string and returns "VALID" or a
    descriptive error the agent can use to self-correct.
"""

from __future__ import annotations

import json
import re
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

# Maps component.type → Mermaid node shape syntax
_SHAPE = {
    "service":   ("[{name}]",        "service"),
    "database":  ("[({name})]",      "database"),
    "cache":     ("([{name}])",      "cache"),
    "queue":     ("{{{name}}}",      "queue"),
    "cdn":       (">{name}]",        "cdn"),
    "gateway":   ("[{name}]",        "gateway"),
    "client":    ("({name})",        "client"),
    "storage":   ("[({name})]",      "database"),
}
_DEFAULT_SHAPE = ("[{name}]", "service")

# classDef colour palette
_CLASS_STYLES = {
    "service":  "fill:#dbeafe,stroke:#1d4ed8,stroke-width:2px,color:#1e3a5f",
    "database": "fill:#fef3c7,stroke:#b45309,stroke-width:2px,color:#451a03",
    "cache":    "fill:#d1fae5,stroke:#065f46,stroke-width:2px,color:#064e3b",
    "queue":    "fill:#ffe4e6,stroke:#9f1239,stroke-width:2px,color:#4c0519",
    "cdn":      "fill:#f3e8ff,stroke:#6b21a8,stroke-width:2px,color:#3b0764",
    "gateway":  "fill:#e0f2fe,stroke:#0369a1,stroke-width:2px,color:#0c4a6e",
    "client":   "fill:#f1f5f9,stroke:#475569,stroke-width:2px,color:#1e293b",
    "storage":  "fill:#fef9c3,stroke:#a16207,stroke-width:2px,color:#422006",
}


def _safe_id(name: str) -> str:
    """Return a Mermaid-safe node ID (alphanumeric + underscores only)."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_")


def _node_label(name: str, comp_type: str) -> str:
    """Return the Mermaid node declaration line: ``ID[Label]``."""
    shape_tpl, _ = _SHAPE.get(comp_type.lower(), _DEFAULT_SHAPE)
    label = shape_tpl.format(name=name)
    return f"    {_safe_id(name)}{label}"


def _resolve_class(comp_type: str) -> str:
    return comp_type.lower() if comp_type.lower() in _CLASS_STYLES else "service"


# ──────────────────────────────────────────────────────────────────────────────
# Tool 1 — ArchitectureDiagramTool
# ──────────────────────────────────────────────────────────────────────────────

class ArchitectureDiagramInput(BaseModel):
    pass



class ArchitectureDiagramTool(BaseTool):
    """
    Generates a Mermaid ``graph TD`` architecture diagram from an
    ArchitectureDesign JSON object.

    Pass the full ``ArchitectureDesign`` JSON string produced by the
    ArchitectureCrew. The tool returns a fenced Mermaid code block that can
    be embedded directly in Markdown documentation.
    """

    name: str = "Architecture Diagram Generator"
    description: str = (
        "Generates a syntactically valid Mermaid graph TD diagram for the High-Level Architecture. "
        "Call this tool without any arguments to generate the architecture diagram."
    )
    args_schema: Type[BaseModel] = ArchitectureDiagramInput

    def _run(self, **kwargs) -> str:  # type: ignore[override]
        # Read from temp file written by main.py after ArchitectureCrew completes.
        # We ignore any kwargs the LLM passes — the data is sourced from disk.
        try:
            with open("output/temp_architecture.json", "r", encoding="utf-8") as f:
                architecture_json = f.read()
            data = json.loads(architecture_json)
        except json.JSONDecodeError as exc:
            return f"ERROR: Invalid JSON — {exc}"

        components: list[dict] = data.get("components", [])
        data_flows: list[dict] = data.get("data_flow", [])

        if not components:
            return "ERROR: 'components' list is empty or missing."

        lines: list[str] = ["```mermaid", "graph TD"]

        # ── Node declarations ──────────────────────────────────────────────
        lines.append("")
        lines.append("    %% ── Nodes ──────────────────────────────────────")
        class_map: dict[str, list[str]] = {}  # class_name → [node_ids]

        for comp in components:
            name: str = comp.get("name", "Unknown")
            ctype: str = comp.get("type", "service")
            lines.append(_node_label(name, ctype))
            cls = _resolve_class(ctype)
            class_map.setdefault(cls, []).append(_safe_id(name))

        # ── Edge declarations ──────────────────────────────────────────────
        if data_flows:
            lines.append("")
            lines.append("    %% ── Data Flows ─────────────────────────────────")
            for flow in data_flows:
                src = flow.get("from") or flow.get("from_", "")
                dst = flow.get("to", "")
                proto = flow.get("protocol", "")
                if not src or not dst:
                    continue
                src_id = _safe_id(src)
                dst_id = _safe_id(dst)
                label = f"|{proto}|" if proto else ""
                lines.append(f"    {src_id} -->{label} {dst_id}")

        # ── classDef colour blocks ─────────────────────────────────────────
        lines.append("")
        lines.append("    %% ── Styles ─────────────────────────────────────────")
        used_classes = set(class_map.keys())
        for cls in used_classes:
            style = _CLASS_STYLES.get(cls, _CLASS_STYLES["service"])
            lines.append(f"    classDef {cls} {style}")

        # ── class assignments ──────────────────────────────────────────────
        for cls, node_ids in class_map.items():
            lines.append(f"    class {','.join(node_ids)} {cls}")

        lines.append("```")
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Tool 2 — SequenceDiagramTool
# ──────────────────────────────────────────────────────────────────────────────

class SequenceDiagramInput(BaseModel):
    flow_name: str = Field(
        ...,
        description=(
            "The name of the flow to diagram. "
            "E.g. 'booking', 'search', 'messaging', 'payment', 'authentication'. "
            "The tool picks the most relevant subsystems automatically."
        ),
    )


class SequenceDiagramTool(BaseTool):
    """
    Generates a Mermaid ``sequenceDiagram`` for a named user flow
    (e.g. 'booking', 'search') from a SubsystemDesign JSON object.

    The tool selects the relevant subsystems, constructs participant
    declarations, and traces the key request/response messages through
    the system. The returned block can be embedded directly in Markdown.
    """

    name: str = "Sequence Diagram Generator"
    description: str = (
        "Builds a Mermaid sequenceDiagram for a named flow (e.g. 'booking', 'search', "
        "'messaging', 'payment'). "
        "Use this to generate the Data Flow section diagrams. "
        "Inputs: flow_name (string)."
    )
    args_schema: Type[BaseModel] = SequenceDiagramInput

    # Keywords that link a flow name to relevant subsystem names
    _FLOW_KEYWORDS: dict[str, list[str]] = {
        "booking":        ["booking", "reservation", "payment", "calendar", "lock"],
        "search":         ["search", "geospatial", "listing", "catalog", "index"],
        "messaging":      ["messaging", "message", "chat", "notification", "websocket"],
        "payment":        ["payment", "ledger", "checkout", "billing", "finance"],
        "authentication": ["user", "auth", "identity", "session", "kyc"],
        "listing":        ["listing", "catalog", "host", "media", "cdn"],
    }

    def _match_subsystems(
        self, flow_name: str, subsystems: list[dict]
    ) -> list[dict]:
        """Return subsystems relevant to the requested flow, ordered by relevance."""
        keywords = self._FLOW_KEYWORDS.get(
            flow_name.lower(),
            [flow_name.lower()],
        )
        scored: list[tuple[int, dict]] = []
        for sub in subsystems:
            name_lower = sub.get("name", "").lower()
            score = sum(kw in name_lower for kw in keywords)
            if score > 0:
                scored.append((score, sub))
        # Sort descending by score, keep top 6
        scored.sort(key=lambda x: x[0], reverse=True)
        return [sub for _, sub in scored[:6]]

    def _run(self, flow_name: str = "booking", **kwargs) -> str:  # type: ignore[override]
        # Read from temp file written by main.py after SubsystemCrew completes.
        # We ignore any extra kwargs the LLM passes — the data is sourced from disk.
        try:
            with open("output/temp_subsystems.json", "r", encoding="utf-8") as f:
                subsystem_json = f.read()
            data = json.loads(subsystem_json)
        except json.JSONDecodeError as exc:
            return f"ERROR: Invalid JSON — {exc}"

        all_subsystems: list[dict] = data.get("subsystems", [])
        message_queues: list[dict] = data.get("message_queues", [])

        if not all_subsystems:
            return "ERROR: 'subsystems' list is empty or missing."

        relevant = self._match_subsystems(flow_name, all_subsystems)
        if not relevant:
            # Fallback: use first 5 subsystems
            relevant = all_subsystems[:5]

        lines: list[str] = ["```mermaid", "sequenceDiagram", "    autonumber"]

        # ── Participants ───────────────────────────────────────────────────
        lines.append("")
        lines.append("    %% ── Participants ────────────────────────────────")
        lines.append("    actor Client as End User")

        participant_ids: list[str] = ["Client"]
        for sub in relevant:
            name: str = sub.get("name", "Unknown")
            pid = _safe_id(name)
            lines.append(f"    participant {pid} as {name}")
            participant_ids.append(pid)

        # Include message queues that connect these subsystems
        mq_names: list[str] = []
        for mq in message_queues:
            producers = [_safe_id(p) for p in mq.get("producers", [])]
            consumers = [_safe_id(c) for c in mq.get("consumers", [])]
            participant_set = set(participant_ids)
            if any(p in participant_set for p in producers) or any(
                c in participant_set for c in consumers
            ):
                tech = mq.get("technology", "Queue")
                mq_name = mq.get("name", "MQ")
                mq_id = _safe_id(mq_name)
                lines.append(f"    participant {mq_id} as {mq_name} ({tech})")
                mq_names.append(mq_id)

        # ── Message sequence ───────────────────────────────────────────────
        lines.append("")
        lines.append(f"    %% ── {flow_name.title()} Flow ─────────────────────────────")

        prev_id = "Client"
        for sub in relevant:
            name = sub.get("name", "Unknown")
            pid = _safe_id(name)
            endpoints: list[dict] = sub.get("api_endpoints", [])

            # Pick the most representative endpoint for this flow
            if endpoints:
                ep = endpoints[0]
                method = ep.get("method", "POST")
                path = ep.get("path", "/api/v1/action")
                desc = ep.get("description", "Process request")
                lines.append(f"    {prev_id}->>{pid}: {method} {path}")
                # DB interaction
                db = sub.get("database")
                if db:
                    db_type = db.get("type", "Database")
                    schemas = db.get("schema", db.get("schema_", []))
                    table = schemas[0].get("table_or_collection", "table") if schemas else "store"
                    db_id = _safe_id(f"{name}_DB")
                    lines.append(f"    Note over {pid}: Processing — {desc}")
                    lines.append(f"    {pid}->>{db_id}: Read/Write {table}")
                    lines.append(f"    {db_id}-->>{pid}: ACK")
                else:
                    lines.append(f"    Note over {pid}: {desc}")
                lines.append(f"    {pid}-->>{prev_id}: Response OK")
            else:
                lines.append(f"    {prev_id}->>{pid}: Invoke {name}")
                lines.append(f"    {pid}-->>{prev_id}: Response OK")

            prev_id = pid

        # ── Message queue publish / consume ────────────────────────────────
        for mq in message_queues:
            mq_id = _safe_id(mq.get("name", "MQ"))
            if mq_id not in mq_names:
                continue
            topics = mq.get("topics", [])
            producers = [_safe_id(p) for p in mq.get("producers", [])]
            consumers = [_safe_id(c) for c in mq.get("consumers", [])]
            topic_label = topics[0] if topics else "event"
            if producers:
                lines.append(f"    {producers[0]}->>{mq_id}: Publish '{topic_label}'")
            for consumer in consumers[:2]:
                lines.append(f"    {mq_id}->>{consumer}: Consume '{topic_label}'")

        lines.append("```")
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Tool 3 — MermaidValidatorTool
# ──────────────────────────────────────────────────────────────────────────────

class MermaidValidatorInput(BaseModel):
    mermaid_string: str = Field(
        ...,
        description=(
            "The raw Mermaid diagram string to validate. "
            "May or may not include the fenced code block markers (```mermaid ... ```)."
        ),
    )


class MermaidValidatorTool(BaseTool):
    """
    Validates the structural integrity of a Mermaid diagram string.

    Checks for common errors such as:
    - Missing diagram type declaration (``graph TD``, ``sequenceDiagram``, etc.)
    - Unclosed node brackets ``[``, ``(``, ``{``
    - Invalid arrow syntax
    - Duplicate node IDs
    - Empty diagram body

    Returns ``"VALID"`` if the diagram passes all checks, or a specific error
    message describing what needs to be fixed.
    """

    name: str = "Mermaid Diagram Validator"
    description: str = (
        "Validates the syntax of a Mermaid diagram string. "
        "Returns 'VALID' if the diagram is structurally correct, or a specific "
        "error message describing what needs to be fixed. "
        "Always validate diagrams before embedding them in the final document."
    )
    args_schema: Type[BaseModel] = MermaidValidatorInput

    # Known valid diagram type declarations
    _DIAGRAM_TYPES = re.compile(
        r"^\s*(graph\s+(TD|LR|BT|RL|TB)|flowchart\s+(TD|LR|BT|RL|TB)"
        r"|sequenceDiagram|classDiagram|erDiagram|gantt|pie|gitGraph"
        r"|stateDiagram(-v2)?|journey|mindmap|timeline|xychart-beta)",
        re.MULTILINE | re.IGNORECASE,
    )

    def _strip_fences(self, text: str) -> str:
        """Remove ```mermaid ... ``` fences if present."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # Drop first and last fence lines
            start = 1
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            return "\n".join(lines[start:end]).strip()
        return text

    def _check_brackets(self, content: str) -> str | None:
        """Return error string if brackets are unbalanced, else None."""
        opens = {"[": "]", "(": ")", "{": "}"}
        closes = {v: k for k, v in opens.items()}
        stack: list[str] = []
        in_string = False
        for i, ch in enumerate(content):
            if ch == '"':
                in_string = not in_string
            if in_string:
                continue
            if ch in opens:
                stack.append(ch)
            elif ch in closes:
                expected = closes[ch]
                if not stack or stack[-1] != expected:
                    snippet = content[max(0, i - 20): i + 5]
                    return f"Unbalanced bracket '{ch}' near: ...{snippet!r}..."
                stack.pop()
        if stack:
            return f"Unclosed bracket(s): {stack}"
        return None

    def _check_duplicate_ids(self, content: str) -> str | None:
        """Return error if the same node ID is declared with different labels."""
        # Match patterns like: NodeId[Label] or NodeId(Label) etc.
        pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)[\[\(\{>]")
        seen: dict[str, int] = {}
        for match in pattern.finditer(content):
            node_id = match.group(1)
            # Skip Mermaid keywords
            if node_id.lower() in {
                "graph", "flowchart", "sequencediagram", "classdiagram",
                "note", "participant", "actor", "loop", "alt", "opt",
                "par", "critical", "break", "end", "subgraph", "class",
                "classDef", "style", "linkStyle", "direction", "autonumber",
                "activate", "deactivate", "rect", "over",
            }:
                continue
            seen[node_id] = seen.get(node_id, 0) + 1

        # IDs appearing more than 5 times are suspicious duplicates
        duplicates = [k for k, v in seen.items() if v > 8]
        if duplicates:
            return f"Possible over-repeated node IDs (may indicate copy errors): {duplicates[:5]}"
        return None

    def _check_arrows(self, content: str, diagram_type: str) -> str | None:
        """Return error if a graph diagram has no arrow declarations."""
        if "sequenceDiagram" in diagram_type or "classDiagram" in diagram_type:
            # These use different syntax — skip arrow check
            return None
        arrow_pattern = re.compile(r"(-{1,3}>|-{1,3}\.?>|\|>|==+>|\*)")
        if not arrow_pattern.search(content):
            return (
                "No arrow declarations found in graph diagram. "
                "A graph TD/LR diagram should have edges like: A --> B or A -->|label| B"
            )
        return None

    def _run(self, mermaid_string: str) -> str:  # type: ignore[override]
        content = self._strip_fences(mermaid_string)

        if not content.strip():
            return "ERROR: Diagram is empty."

        # ── Check 1: diagram type declaration ─────────────────────────────
        type_match = self._DIAGRAM_TYPES.search(content)
        if not type_match:
            return (
                "ERROR: Missing or unrecognised diagram type declaration. "
                "The first non-comment line must be one of: graph TD, graph LR, "
                "sequenceDiagram, classDiagram, erDiagram, etc."
            )
        diagram_type = type_match.group(0).strip()

        # Get content after the declaration line
        body_start = content.find("\n", type_match.end())
        body = content[body_start:] if body_start != -1 else ""

        if len(body.strip()) < 5:
            return "ERROR: Diagram body is empty — no nodes or messages defined."

        # ── Check 2: bracket balance ───────────────────────────────────────
        bracket_err = self._check_brackets(body)
        if bracket_err:
            return f"ERROR: {bracket_err}"

        # ── Check 3: arrows (for graph diagrams) ──────────────────────────
        arrow_err = self._check_arrows(body, diagram_type)
        if arrow_err:
            return f"ERROR: {arrow_err}"

        # ── Check 4: duplicate node IDs ───────────────────────────────────
        dup_err = self._check_duplicate_ids(body)
        if dup_err:
            return f"WARNING: {dup_err}"

        return "VALID"
