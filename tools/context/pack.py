from __future__ import annotations

import argparse
import json
import math
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

DEFAULT_CONFIG: Dict[str, MutableMapping[str, float]] = {
    "pagerank": {"lambda": 0.85, "theta": 0.6},
    "weights": {"intent": 0.40, "diff": 0.25, "recency": 0.20, "hub": 0.10, "role": 0.05},
    "recency_halflife_days": 45,
    "diversity": {"mu_file": 0.15, "mu_role": 0.10},
    "limits": {"ncand": 2000, "iters": 50, "tol": 1e-6},
}


def load_config(path: Path | None = None) -> Dict[str, MutableMapping[str, float]]:
    target = path or Path("tools/context/config.yaml")
    if not target.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))
    return _parse_simple_yaml(target.read_text())


def _parse_simple_yaml(text: str) -> Dict[str, MutableMapping[str, float]]:
    root: Dict[str, MutableMapping[str, float]] = {}
    stack: List[tuple[int, MutableMapping[str, float]]] = [(0, root)]
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        while stack and indent < stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        key, _, rest = line.partition(":")
        key = key.strip()
        value = rest.strip()
        if not value:
            node: MutableMapping[str, float] = {}
            parent[key] = node
            stack.append((indent + 2, node))
        else:
            parent[key] = _coerce_scalar(value)
    return root


def _coerce_scalar(value: str):
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(ch in value for ch in ".eE"):
            return float(value)
        return int(value)
    except ValueError:
        return value


def _token_set(*parts: str) -> set[str]:
    tokens: set[str] = set()
    for part in parts:
        for piece in part.replace("/", " ").replace("-", " ").split():
            clean = "".join(ch for ch in piece.lower() if ch.isalnum())
            if clean:
                tokens.add(clean)
    return tokens


def _intent_profile(intent: str, halflife: int) -> Dict[str, object]:
    tokens = _token_set(intent)
    role = next((r for r in ["impl", "ops", "risk", "spec"] if r in tokens), None)
    keywords = sorted(tokens - {"int", "intent"})
    return {"keywords": keywords, "role": role, "halflife": halflife}


def _recency_score(iso_ts: str, halflife: int) -> float:
    mt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    age = max(0.0, (datetime.now(timezone.utc) - mt).total_seconds() / 86400)
    return math.exp(-age / max(halflife, 1))


def _hub_scores(nodes: Sequence[Mapping[str, object]], edges: Sequence[Mapping[str, str]]) -> Dict[str, float]:
    degree: Counter[str] = Counter()
    for edge in edges:
        degree[edge["src"]] += 1
    max_deg = max(degree.values(), default=1)
    result: Dict[str, float] = {}
    for node in nodes:
        out_deg = degree.get(node["id"], 0)
        result[node["id"]] = math.log1p(out_deg) / math.log1p(max_deg) if max_deg else 0.0
    return result


def _role_weight(node_role: str | None, intent_role: str | None) -> float:
    if not intent_role:
        return 0.4
    if node_role == intent_role:
        return 0.6
    return 0.2


def _intent_hit(keywords: Sequence[str], node_tokens: set[str]) -> float:
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in node_tokens)
    return hits / len(keywords)


def _diff_hit(path: str, diff_paths: Sequence[str]) -> float:
    if not diff_paths:
        return 0.0
    if path in diff_paths:
        return 1.0
    directories = {d.rsplit("/", 1)[0] for d in diff_paths if "/" in d}
    if any(path.startswith(dir_path + "/") or path == dir_path for dir_path in directories):
        return 0.7
    domains = {d.split("/", 1)[0] for d in diff_paths}
    if any(path.startswith(domain) for domain in domains):
        return 0.4
    return 0.0


def personalize_scores(
    nodes: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, str]],
    base_scores: Mapping[str, float],
    lam: float,
    iters: int,
    tol: float,
) -> Dict[str, float]:
    n = len(nodes)
    if n == 0:
        return {}
    id_to_index = {node["id"]: idx for idx, node in enumerate(nodes)}
    adjacency = [[] for _ in range(n)]
    outdeg = [0] * n
    for edge in edges:
        src = id_to_index.get(edge["src"])
        dst = id_to_index.get(edge["dst"])
        if src is None or dst is None:
            continue
        adjacency[src].append(dst)
        outdeg[src] += 1
    teleport = [max(base_scores.get(node["id"], 0.0), 0.0) for node in nodes]
    total = sum(teleport) or 1.0
    teleport = [value / total for value in teleport]
    state = [1.0 / n] * n
    for _ in range(iters):
        updated = [(1 - lam) * teleport[i] for i in range(n)]
        for i, row in enumerate(adjacency):
            share = lam * state[i] / (outdeg[i] or n)
            if outdeg[i] == 0:
                for j in range(n):
                    updated[j] += share
            else:
                for j in row:
                    updated[j] += share
        delta = sum(abs(updated[i] - state[i]) for i in range(n))
        state = updated
        if delta < tol:
            break
    normaliser = sum(state) or 1.0
    return {nodes[i]["id"]: state[i] / normaliser for i in range(n)}


def _candidate_ids(
    hits: Iterable[str],
    adjacency: Dict[str, List[str]],
    reverse_adj: Dict[str, List[str]],
    max_hops: int,
) -> set[str]:
    seen: set[str] = set()
    queue = deque((node, 0) for node in hits)
    while queue:
        node, dist = queue.popleft()
        if node in seen or dist > max_hops:
            continue
        seen.add(node)
        for nxt in adjacency.get(node, []):
            queue.append((nxt, dist + 1))
        for nxt in reverse_adj.get(node, []):
            queue.append((nxt, dist + 1))
    return seen


def _token_budget(node: Mapping[str, object]) -> int:
    if "token_estimate" in node:
        return int(node["token_estimate"])
    heading = node.get("heading", "")
    return max(32, len(heading.split()) * 10)


def _diversity_penalty(
    path: str,
    role: str | None,
    path_counter: Counter[str],
    role_counter: Counter[str],
    total_selected: int,
    mu_file: float,
    mu_role: float,
) -> float:
    if total_selected == 0:
        return 1.0
    file_ratio = path_counter[path] / total_selected if total_selected else 0.0
    role_ratio = role_counter[role or "unknown"] / total_selected if total_selected else 0.0
    penalty = 1.0 - (mu_file * file_ratio + mu_role * role_ratio)
    return max(0.1, penalty)


def pack_graph(
    graph_path: Path,
    intent: str,
    budget_tokens: int,
    diff_paths: Sequence[str],
    config: Mapping[str, Mapping[str, float]] | None = None,
) -> Dict[str, object]:
    config = config or load_config()
    graph = json.loads(Path(graph_path).read_text())
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    halflife = int(config.get("recency_halflife_days", 45))
    intent_profile = _intent_profile(intent, halflife)
    hub_scores = _hub_scores(nodes, edges)
    adjacency: Dict[str, List[str]] = {}
    reverse_adj: Dict[str, List[str]] = {}
    node_tokens: Dict[str, set[str]] = {}
    base_signals: Dict[str, Dict[str, float]] = {}
    hits: list[str] = []
    diff_paths = list(diff_paths)
    for edge in edges:
        adjacency.setdefault(edge["src"], []).append(edge["dst"])
        reverse_adj.setdefault(edge["dst"], []).append(edge["src"])
    for node in nodes:
        tokens = _token_set(node.get("heading", ""), node.get("path", ""))
        node_tokens[node["id"]] = tokens
        intent_hit = _intent_hit(intent_profile["keywords"], tokens)
        diff_hit = _diff_hit(node.get("path", ""), diff_paths)
        recency = _recency_score(node.get("mtime", datetime.now(timezone.utc).isoformat()), halflife)
        hub = hub_scores.get(node["id"], 0.0)
        role_score = _role_weight(node.get("role"), intent_profile["role"])
        base_signals[node["id"]] = {
            "intent": intent_hit,
            "diff": diff_hit,
            "recency": recency,
            "hub": hub,
            "role": role_score,
        }
        if intent_hit > 0 or diff_hit > 0:
            hits.append(node["id"])
    weights = config.get("weights", {})
    base_scores = {
        node_id: sum(base_signals[node_id][key] * float(weights.get(key, 0.0)) for key in base_signals[node_id])
        for node_id in base_signals
    }
    candidates = _candidate_ids(hits, adjacency, reverse_adj, 2) if hits else set(base_scores.keys())
    sorted_candidates = sorted(candidates, key=lambda nid: base_scores.get(nid, 0.0), reverse=True)
    ncand = int(config.get("limits", {}).get("ncand", 2000))
    selected_candidates = sorted_candidates[:ncand]
    candidate_nodes = [node for node in nodes if node["id"] in selected_candidates]
    if not candidate_nodes:
        candidate_nodes = nodes
    pagerank_cfg = config.get("pagerank", {})
    ppr_scores = personalize_scores(
        candidate_nodes,
        edges,
        base_scores,
        float(pagerank_cfg.get("lambda", 0.85)),
        int(config.get("limits", {}).get("iters", 50)),
        float(config.get("limits", {}).get("tol", 1e-6)),
    )
    theta = float(pagerank_cfg.get("theta", 0.6))
    scores = {
        node["id"]: theta * ppr_scores.get(node["id"], 0.0) + (1 - theta) * base_scores.get(node["id"], 0.0)
        for node in candidate_nodes
    }
    ranked_nodes = sorted(candidate_nodes, key=lambda node: scores.get(node["id"], 0.0), reverse=True)
    path_counter: Counter[str] = Counter()
    role_counter: Counter[str] = Counter()
    sections = []
    token_in = 0
    token_src = sum(_token_budget(node) for node in ranked_nodes)
    diversity_cfg = config.get("diversity", {})
    mu_file = float(diversity_cfg.get("mu_file", 0.15))
    mu_role = float(diversity_cfg.get("mu_role", 0.10))
    total_penalty = 0.0
    for node in ranked_nodes:
        tokens = _token_budget(node)
        if token_in + tokens > budget_tokens:
            continue
        penalty = _diversity_penalty(
            node.get("path", ""),
            node.get("role"),
            path_counter,
            role_counter,
            len(sections),
            mu_file,
            mu_role,
        )
        adjusted = scores.get(node["id"], 0.0) * penalty
        total_penalty += 1 - penalty
        sections.append(
            {
                "id": node["id"],
                "tok": tokens,
                "filters": ["lossless", "pointer", "role_extract"],
                "why": {
                    "intent": base_signals[node["id"]]["intent"],
                    "diff": base_signals[node["id"]]["diff"],
                    "recency": base_signals[node["id"]]["recency"],
                    "hub": base_signals[node["id"]]["hub"],
                    "role": base_signals[node["id"]]["role"],
                    "ppr": ppr_scores.get(node["id"], 0.0),
                    "score": adjusted,
                },
            }
        )
        token_in += tokens
        path_counter[node.get("path", "")] += 1
        role_counter[node.get("role", "unknown")] += 1
    diversity_penalty = total_penalty / max(len(sections), 1)
    ppr_values = [ppr_scores.get(node["id"], 0.0) for node in candidate_nodes]
    normaliser = sum(ppr_values) or 1.0
    entropy = -sum((val / normaliser) * math.log(val / normaliser) for val in ppr_values if val > 0)
    dup_rate = 0.0
    if sections:
        unique_paths = {section["id"].split("#", 1)[0] for section in sections}
        dup_rate = 1.0 - len(unique_paths) / len(sections)
    metrics = {
        "token_in": token_in,
        "token_src": token_src,
        "dup_rate": dup_rate,
        "ppr_entropy": entropy,
        "diversity_penalty": diversity_penalty,
    }
    return {"intent": intent, "budget": str(budget_tokens), "sections": sections, "metrics": metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate context packs with PPR scoring")
    parser.add_argument("--graph", type=Path, default=Path("reports/context/graph.json"))
    parser.add_argument("--intent", required=True)
    parser.add_argument("--budget", type=int, default=2000)
    parser.add_argument("--diff", type=Path, nargs="*", default=[])
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("reports/context/pack.json"))
    args = parser.parse_args()
    diff_paths = []
    for diff in args.diff:
        diff_paths.extend(diff.read_text().splitlines())
    config = load_config(args.config) if args.config else load_config()
    result = pack_graph(args.graph, args.intent, args.budget, diff_paths, config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
