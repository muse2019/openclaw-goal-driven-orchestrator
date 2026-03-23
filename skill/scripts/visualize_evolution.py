#!/usr/bin/env python3
"""
Plan DAG Visualization Script

Generates an interactive HTML visualization of the research/experiment plan.

Usage:
    python scripts/visualize_evolution.py .autoresearch/plan.json

Output:
    Creates .autoresearch/plan_graph.html
"""

import json
import sys
import os
from datetime import datetime
from typing import Optional

def load_dag(dag_path: str) -> dict:
    with open(dag_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_type_shape(node_type: str) -> str:
    shapes = {
        'research': 'rect',
        'experiment': 'circle',
        'verification': 'diamond',
        'synthesis': 'hexagon',
    }
    return shapes.get(node_type, 'rect')

def get_status_color(node: dict) -> str:
    status = node.get('status', 'pending')
    confidence = None
    if node.get('finding'):
        confidence = node['finding'].get('confidence')
    elif node.get('result'):
        confidence = node.get('status')

    # Confidence takes priority for coloring
    if confidence == 'verified' or status == 'pass':
        return '#22c55e'      # bright green
    if confidence == 'refuted' or status == 'fail':
        return '#ef4444'      # red
    if confidence == 'theoretical':
        return '#eab308'      # yellow

    colors = {
        'pending': '#9ca3af',      # gray
        'running': '#3b82f6',      # blue
        'answered': '#22c55e',     # green
        'partial': '#f97316',      # orange
        'unanswerable': '#a855f7', # purple
        'completed': '#22c55e',    # green
        'failed': '#ef4444',       # red
        'error': '#dc2626',        # dark red
        'superseded': '#6b7280',   # dim gray
    }
    return colors.get(status, '#9ca3af')

def get_node_label(node_id: str, node: dict) -> str:
    ntype = node.get('type', '?')
    prefix = {'research': 'R', 'experiment': 'E', 'verification': 'V', 'synthesis': 'S'}.get(ntype, '?')

    if ntype == 'research' or ntype == 'synthesis':
        text = node.get('question', '')
    elif ntype == 'experiment':
        text = node.get('hypothesis', '')
    elif ntype == 'verification':
        text = node.get('question', '')
    else:
        text = node_id

    # Truncate for display
    if len(text) > 40:
        text = text[:37] + '...'

    return f"[{prefix}] {text}"

def generate_node_details(node_id: str, node: dict) -> str:
    ntype = node.get('type', 'unknown')
    status = node.get('status', 'pending')

    html = f'<div class="detail-panel">'
    html += f'<h3>{node_id}</h3>'
    html += f'<p><b>Type:</b> {ntype}</p>'
    html += f'<p><b>Status:</b> <span class="badge" style="background:{get_status_color(node)}">{status}</span></p>'

    if ntype == 'research':
        html += f'<p><b>Question:</b> {node.get("question", "")}</p>'
        html += f'<p><b>Approach:</b> {node.get("approach", "")}</p>'
        if node.get('finding'):
            f = node['finding']
            html += f'<p><b>Summary:</b> {f.get("summary", "")}</p>'
            html += f'<p><b>Confidence:</b> {f.get("confidence", "")}</p>'
            if f.get('evidence'):
                html += '<p><b>Evidence:</b></p><ul>'
                for e in f['evidence']:
                    html += f'<li>{e}</li>'
                html += '</ul>'
            html += f'<p><b>Verifiable:</b> {f.get("verifiable", False)}</p>'

    elif ntype == 'experiment':
        html += f'<p><b>Hypothesis:</b> {node.get("hypothesis", "")}</p>'
        html += f'<p><b>Metric:</b> {node.get("metric", "")}</p>'
        html += f'<p><b>Pass condition:</b> {node.get("pass_condition", "")}</p>'
        if node.get('result'):
            r = node['result']
            html += f'<p><b>Metric value:</b> {r.get("metric_value", "N/A")}</p>'
            html += f'<p><b>Command:</b> <code>{r.get("verification_command", "")}</code></p>'

    elif ntype == 'verification':
        html += f'<p><b>Claim:</b> {node.get("question", "")}</p>'
        html += f'<p><b>Metric:</b> {node.get("metric", "")}</p>'
        html += f'<p><b>Pass condition:</b> {node.get("pass_condition", "")}</p>'
        if node.get('result'):
            r = node['result']
            html += f'<p><b>Result:</b> {r.get("metric_value", "N/A")}</p>'

    elif ntype == 'synthesis':
        if node.get('finding'):
            f = node['finding']
            html += f'<p><b>Summary:</b> {f.get("summary", "")}</p>'
            if f.get('recommendations'):
                html += '<p><b>Recommendations:</b></p><ol>'
                for rec in f['recommendations']:
                    html += f'<li>{rec}</li>'
                html += '</ol>'

    if node.get('started_at'):
        html += f'<p class="timestamp">Started: {node["started_at"]}</p>'
    if node.get('completed_at'):
        html += f'<p class="timestamp">Completed: {node["completed_at"]}</p>'

    html += '</div>'
    return html

def assign_positions(nodes: dict) -> dict:
    """Assign x,y positions using topological sort + layering."""
    positions = {}
    layers = {}

    # Calculate depth for each node
    def get_depth(nid, visited=None):
        if visited is None:
            visited = set()
        if nid in visited:
            return 0
        visited.add(nid)
        parents = nodes[nid].get('parent_ids', [])
        if not parents:
            return 0
        return 1 + max(get_depth(p, visited) for p in parents if p in nodes)

    for nid in nodes:
        depth = get_depth(nid)
        layers.setdefault(depth, []).append(nid)

    # Assign positions
    for depth, layer_nodes in layers.items():
        y = depth * 150 + 50
        total_width = len(layer_nodes) * 200
        start_x = max(50, (900 - total_width) // 2)
        for i, nid in enumerate(layer_nodes):
            x = start_x + i * 200
            positions[nid] = (x, y)

    return positions

def generate_html(dag: dict) -> str:
    nodes = dag.get('nodes', {})
    metadata = dag.get('metadata', {})
    stats = dag.get('statistics', {})
    positions = assign_positions(nodes)

    # Canvas size
    max_x = max((p[0] for p in positions.values()), default=400) + 200
    max_y = max((p[1] for p in positions.values()), default=300) + 200

    html = f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Plan: {metadata.get("goal", "Unknown")}</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
.header {{ padding: 20px; background: #1e293b; border-bottom: 1px solid #334155; }}
.header h1 {{ margin: 0; font-size: 1.4em; }}
.header .meta {{ color: #94a3b8; font-size: 0.9em; margin-top: 5px; }}
.stats {{ display: flex; gap: 20px; margin-top: 10px; }}
.stat {{ background: #334155; padding: 6px 14px; border-radius: 6px; font-size: 0.85em; }}
.canvas-wrap {{ overflow: auto; padding: 20px; }}
svg {{ cursor: grab; }}
svg text {{ font-family: 'Segoe UI', sans-serif; font-size: 12px; fill: #e2e8f0; }}
.node {{ cursor: pointer; transition: opacity 0.2s; }}
.node:hover {{ opacity: 0.85; }}
.edge {{ stroke: #475569; stroke-width: 2; fill: none; marker-end: url(#arrow); }}
.badge {{ padding: 2px 8px; border-radius: 4px; color: #fff; font-size: 0.8em; }}
.detail-panel {{ position: fixed; right: 20px; top: 80px; width: 350px; background: #1e293b;
  border: 1px solid #334155; border-radius: 8px; padding: 20px; display: none; z-index: 100;
  max-height: 80vh; overflow-y: auto; }}
.detail-panel h3 {{ margin-top: 0; color: #60a5fa; }}
.detail-panel p {{ margin: 6px 0; line-height: 1.4; }}
.detail-panel code {{ background: #334155; padding: 2px 6px; border-radius: 3px; }}
.detail-panel ul, .detail-panel ol {{ padding-left: 20px; }}
.timestamp {{ color: #64748b; font-size: 0.8em; }}
.legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; }}
.legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 0.8em; }}
.legend-shape {{ width: 16px; height: 16px; }}
</style></head><body>

<div class="header">
  <h1>📊 {metadata.get("goal", "Plan Visualization")}</h1>
  <div class="meta">Type: {metadata.get("goal_type", "?")} | Budget: {metadata.get("time_budget_minutes", "?")} min</div>
  <div class="stats">
    <span class="stat">Total: {stats.get("total_nodes", len(nodes))}</span>
    <span class="stat">✅ Done: {stats.get("completed_count", 0)}</span>
    <span class="stat">⏳ Pending: {stats.get("pending_count", 0)}</span>
    <span class="stat">❌ Errors: {stats.get("error_count", 0)}</span>
  </div>
  <div class="legend">
    <div class="legend-item"><svg width="16" height="16"><rect x="2" y="2" width="12" height="12" fill="#60a5fa" rx="2"/></svg> Research</div>
    <div class="legend-item"><svg width="16" height="16"><circle cx="8" cy="8" r="6" fill="#f59e0b"/></svg> Experiment</div>
    <div class="legend-item"><svg width="16" height="16"><polygon points="8,2 14,8 8,14 2,8" fill="#a78bfa"/></svg> Verification</div>
    <div class="legend-item"><svg width="16" height="16"><polygon points="8,2 14,5 14,11 8,14 2,11 2,5" fill="#f472b6"/></svg> Synthesis</div>
  </div>
</div>

<div class="canvas-wrap">
<svg width="{max_x}" height="{max_y}">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"
    markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
  </marker>
</defs>
'''

    # Draw edges
    for nid, node in nodes.items():
        if nid not in positions:
            continue
        x2, y2 = positions[nid]
        for pid in node.get('parent_ids', []):
            if pid in positions:
                x1, y1 = positions[pid]
                html += f'<line class="edge" x1="{x1}" y1="{y1+25}" x2="{x2}" y2="{y2-25}"/>\n'

    # Draw nodes
    for nid, node in nodes.items():
        if nid not in positions:
            continue
        x, y = positions[nid]
        color = get_status_color(node)
        ntype = node.get('type', 'research')
        label = get_node_label(nid, node)

        html += f'<g class="node" onclick="showDetail(\'{nid}\')" transform="translate({x},{y})">\n'

        if ntype == 'research' or ntype == 'synthesis':
            html += f'  <rect x="-70" y="-20" width="140" height="40" rx="6" fill="{color}" opacity="0.9"/>\n'
        elif ntype == 'experiment':
            html += f'  <circle cx="0" cy="0" r="28" fill="{color}" opacity="0.9"/>\n'
        elif ntype == 'verification':
            html += f'  <polygon points="0,-28 28,0 0,28 -28,0" fill="{color}" opacity="0.9"/>\n'
        else:
            html += f'  <rect x="-70" y="-20" width="140" height="40" rx="6" fill="{color}" opacity="0.9"/>\n'

        # Label (truncate more for circles/diamonds)
        display_text = label[:20] + '...' if len(label) > 20 and ntype in ('experiment', 'verification') else label[:30]
        html += f'  <text x="0" y="5" text-anchor="middle" font-size="11">{display_text}</text>\n'
        html += '</g>\n'

    html += '</svg></div>\n'

    # Detail panels (hidden, shown on click)
    html += '<div id="detailPanel" class="detail-panel"></div>\n'
    html += '<script>\n'
    html += 'const details = {\n'
    for nid, node in nodes.items():
        detail = generate_node_details(nid, node).replace("'", "\\'").replace('\n', '\\n')
        html += f"  '{nid}': '{detail}',\n"
    html += '};\n'
    html += '''
function showDetail(id) {
  const panel = document.getElementById("detailPanel");
  panel.innerHTML = details[id] || "<p>No details</p>";
  panel.style.display = "block";
}
document.addEventListener("click", function(e) {
  if (!e.target.closest(".node") && !e.target.closest(".detail-panel")) {
    document.getElementById("detailPanel").style.display = "none";
  }
});
</script>
'''
    html += '</body></html>'
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_evolution.py <plan.json>")
        sys.exit(1)

    dag_path = sys.argv[1]
    if not os.path.exists(dag_path):
        print(f"File not found: {dag_path}")
        sys.exit(1)

    dag = load_dag(dag_path)
    html = generate_html(dag)

    output_dir = os.path.dirname(dag_path)
    output_path = os.path.join(output_dir, 'plan_graph.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Visualization saved to {output_path}")

if __name__ == '__main__':
    main()
