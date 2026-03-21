#!/usr/bin/env python3
"""
Evolution DAG Visualization Script

Generates an interactive HTML visualization of the experiment evolution graph.

Usage:
    python scripts/visualize_evolution.py .autoresearch/evolution_dag.json

Output:
    Creates .autoresearch/evolution_graph.html
"""

import json
import sys
import os
from datetime import datetime
from typing import Optional

def load_dag(dag_path: str) -> dict:
    with open(dag_path, 'r') as f:
        return json.load(f)

def get_status_color(status: str) -> str:
    colors = {
        'pending': '#9ca3af',    # gray
        'running': '#3b82f6',    # blue
        'success': '#22c55e',    # green
        'dead_end': '#ef4444',  # red
    }
    return colors.get(status, '#9ca3af')

def get_best_path(dag: dict) -> list:
    """Get the path from root to best node."""
    if not dag.get('best_node_id'):
        return []
    
    path = []
    current = dag['best_node_id']
    visited = set()
    
    while current and current not in visited:
        path.append(current)
        visited.add(current)
        parents = dag['nodes'][current].get('parent_ids', [])
        current = parents[0] if parents else None
    
    return list(reversed(path))

def generate_node_details(node_id: str, node: dict) -> str:
    """Generate HTML for node details panel."""
    result = node.get('result', {})
    metric = result.get('metric', 'N/A')
    delta = result.get('delta', 'N/A')
    duration = result.get('duration_seconds', 'N/A')
    insights = node.get('insights', [])
    created = node.get('created_at', 'N/A')
    started = node.get('started_at', 'N/A')
    completed = node.get('completed_at', 'N/A')
    
    insights_html = ''
    if insights:
        insights_html = '<h4>Insights:</h4><ul>'
        for insight in insights:
            insights_html += f'<li>{insight}</li>'
        insights_html += '</ul>'
    
    return f"""
    <div class="node-details" id="details-{node_id}">
        <h3>{node_id}</h3>
        <p><strong>Status:</strong> {node.get('status', 'unknown')}</p>
        <p><strong>Hypothesis:</strong> {node.get('hypothesis', 'N/A')}</p>
        <p><strong>Action:</strong> {node.get('action', 'N/A')}</p>
        <h4>Result:</h4>
        <ul>
            <li>Metric: {metric}</li>
            <li>Delta: {delta}</li>
            <li>Duration: {duration}s</li>
        </ul>
        {insights_html}
        <h4>Timestamps:</h4>
        <ul>
            <li>Created: {created}</li>
            <li>Started: {started}</li>
            <li>Completed: {completed}</li>
        </ul>
    </div>
    """

def generate_html(dag: dict, output_path: str):
    """Generate the HTML visualization."""
    nodes = dag.get('nodes', {})
    metadata = dag.get('metadata', {})
    stats = dag.get('statistics', {})
    best_path = set(get_best_path(dag))
    
    # Generate nodes and edges
    node_htmls = []
    edge_lines = []
    
    for node_id, node in nodes.items():
        status = node.get('status', 'pending')
        color = get_status_color(status)
        is_best = node_id in best_path
        best_style = 'stroke: gold; stroke-width: 3px;' if is_best else ''
        
        parent_ids = node.get('parent_ids', [])
        
        # Node circle
        node_htmls.append(f'''
        <div class="node" id="node-{node_id}" 
             style="left: {hash(node_id) % 600 + 50}px; top: {hash(node_id + 'y') % 400 + 50}px; 
                    background-color: {color}; {best_style}"
             onclick="showDetails('{node_id}')"
             data-node-id="{node_id}">
            <span class="node-label">{node_id}</span>
        </div>
        ''')
        
        # Edges from parents
        for parent_id in parent_ids:
            if parent_id in nodes:
                edge_lines.append(f'''
                // Edge: {parent_id} -> {node_id}
                drawEdge('node-{parent_id}', 'node-{node_id}', '{color}');
                ''')
    
    # Statistics
    stats_html = f'''
    <div class="stats">
        <h3>Statistics</h3>
        <p>Total nodes: {stats.get('total_nodes', 0)}</p>
        <p>Success: {stats.get('success_count', 0)}</p>
        <p>Dead ends: {stats.get('dead_end_count', 0)}</p>
        <p>Pending: {stats.get('pending_count', 0)}</p>
        <p>Running: {stats.get('running_count', 0)}</p>
    </div>
    '''
    
    # Node details
    details_html = ''
    for node_id, node in nodes.items():
        details_html += generate_node_details(node_id, node)
    
    # Legend
    legend_html = '''
    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item"><span class="dot" style="background: #22c55e"></span> Success</div>
        <div class="legend-item"><span class="dot" style="background: #ef4444"></span> Dead End</div>
        <div class="legend-item"><span class="dot" style="background: #3b82f6"></span> Running</div>
        <div class="legend-item"><span class="dot" style="background: #9ca3af"></span> Pending</div>
        <div class="legend-item"><span class="dot" style="background: #22c55e; border: 2px solid gold"></span> Best Path</div>
    </div>
    '''
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evolution DAG Visualization</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        .container {{ 
            display: flex; 
            height: 100vh;
        }}
        .sidebar {{
            width: 280px;
            background: #16213e;
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid #0f3460;
        }}
        .main {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        .graph {{
            width: 100%;
            height: 100%;
            position: relative;
        }}
        .node {{
            position: absolute;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        .node:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 12px rgba(0,0,0,0.5);
        }}
        .node-label {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 50px;
        }}
        .stats, .legend {{
            margin-bottom: 20px;
        }}
        .stats h3, .legend h3 {{
            margin-bottom: 10px;
            color: #e94560;
        }}
        .stats p, .legend-item {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .dot {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: inline-block;
        }}
        .details-panel {{
            position: absolute;
            right: 20px;
            top: 20px;
            width: 300px;
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
            max-height: calc(100vh - 40px);
            overflow-y: auto;
            display: none;
            border: 1px solid #0f3460;
        }}
        .details-panel.visible {{
            display: block;
        }}
        .details-panel h3 {{
            color: #e94560;
            margin-bottom: 10px;
        }}
        .details-panel h4 {{
            color: #0f3460;
            margin: 15px 0 5px;
        }}
        .details-panel p, .details-panel li {{
            font-size: 13px;
            line-height: 1.5;
        }}
        .close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: none;
            border: none;
            color: #888;
            font-size: 20px;
            cursor: pointer;
        }}
        .close-btn:hover {{
            color: #fff;
        }}
        .metadata {{
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #0f3460;
        }}
        .metadata h2 {{
            color: #e94560;
            margin-bottom: 10px;
        }}
        .metadata p {{
            font-size: 13px;
            margin: 3px 0;
        }}
        .edge {{ 
            position: absolute; 
            pointer-events: none;
            z-index: 0;
        }}
        .edge-line {{
            stroke-width: 2;
            fill: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="metadata">
                <h2>Evolution DAG</h2>
                <p><strong>Goal:</strong> {metadata.get('goal', 'N/A')}</p>
                <p><strong>Criteria:</strong> {metadata.get('success_criteria', 'N/A')}</p>
                <p><strong>Time Budget:</strong> {metadata.get('time_budget_minutes', 'N/A')} min</p>
                <p><strong>Created:</strong> {metadata.get('created_at', 'N/A')}</p>
            </div>
            {stats_html}
            {legend_html}
        </div>
        <div class="main">
            <div class="graph" id="graph">
                <svg id="edges" style="position: absolute; width: 100%; height: 100%;"></svg>
                {''.join(node_htmls)}
            </div>
            <div class="details-panel" id="detailsPanel">
                <button class="close-btn" onclick="hideDetails()">×</button>
                <div id="detailsContent"></div>
            </div>
        </div>
    </div>
    <script>
        function showDetails(nodeId) {{
            const details = document.getElementById('details-' + nodeId);
            const content = document.getElementById('detailsContent');
            const panel = document.getElementById('detailsPanel');
            
            if (details) {{
                content.innerHTML = details.innerHTML;
                panel.classList.add('visible');
            }}
        }}
        
        function hideDetails() {{
            document.getElementById('detailsPanel').classList.remove('visible');
        }}
        
        function drawEdge(fromId, toId, color) {{
            const from = document.getElementById(fromId);
            const to = document.getElementById(toId);
            if (!from || !to) return;
            
            const graph = document.getElementById('graph');
            const graphRect = graph.getBoundingClientRect();
            
            const fromRect = from.getBoundingClientRect();
            const toRect = to.getBoundingClientRect();
            
            const x1 = fromRect.left + fromRect.width / 2;
            const y1 = fromRect.top + fromRect.height / 2;
            const x2 = toRect.left + toRect.width / 2;
            const y2 = toRect.top + toRect.height / 2;
            
            const svg = document.getElementById('edges');
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1 - graphRect.left);
            line.setAttribute('y1', y1 - graphRect.top);
            line.setAttribute('x2', x2 - graphRect.left);
            line.setAttribute('y2', y2 - graphRect.top);
            line.setAttribute('stroke', color);
            line.setAttribute('opacity', '0.5');
            line.classList.add('edge-line');
            svg.appendChild(line);
        }}
        
        // Draw edges after nodes are positioned
        window.addEventListener('load', function() {{
            setTimeout(function() {{
                {''.join(edge_lines)}
            }}, 100);
        }});
        
        // Redraw edges on resize
        window.addEventListener('resize', function() {{
            const svg = document.getElementById('edges');
            svg.innerHTML = '';
            {''.join(edge_lines)}
        }});
    </script>
</body>
</html>
    '''
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Visualization saved to: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/visualize_evolution.py <dag.json>")
        sys.exit(1)
    
    dag_path = sys.argv[1]
    
    if not os.path.exists(dag_path):
        print(f"Error: DAG file not found: {dag_path}")
        sys.exit(1)
    
    # Determine output path
    dag_dir = os.path.dirname(dag_path)
    output_path = os.path.join(dag_dir, 'evolution_graph.html')
    
    # Load and visualize
    dag = load_dag(dag_path)
    generate_html(dag, output_path)
    print(f"Done! Open {output_path} in a browser.")

if __name__ == '__main__':
    main()
