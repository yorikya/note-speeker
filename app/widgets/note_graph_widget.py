from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivy.uix.label import Label
import json
import os
import tempfile
import webbrowser
from bidi.algorithm import get_display
from kivy.clock import Clock
from kivy.lang import Builder

Builder.load_string('''
<NoteGraphWidget>:
    orientation: 'vertical'
    MDCard:
        id: web_container
        size_hint: 1, 1
        md_bg_color: 0, 0, 0, 0
        radius: [15, 15, 15, 15]
        padding: dp(10)
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(10)
            MDLabel:
                text: "Graph Visualization"
                halign: "center"
                size_hint_y: None
                height: dp(40)
            MDRaisedButton:
                text: "Open Graph in Browser"
                pos_hint: {'center_x': .5}
                on_release: root.open_graph()
            Widget:
                size_hint_y: 0.8
''')

class NoteGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_note = None
        self.node_positions = []
        self.html_file = None
        
        # Create HTML template
        self.html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    margin: 0;
                    overflow: hidden;
                    background: #1a1a1a;
                    font-family: 'Alef', sans-serif;
                }
                #graph {
                    width: 100vw;
                    height: 100vh;
                }
                .node {
                    cursor: pointer;
                }
                .node circle {
                    fill: #3366cc;
                    stroke: #fff;
                    stroke-width: 2px;
                }
                .node.selected circle {
                    stroke: #4CAF50;
                    stroke-width: 3px;
                }
                .node text {
                    font-size: 14px;
                    fill: white;
                    text-anchor: middle;
                    dominant-baseline: middle;
                }
                .link {
                    fill: none;
                    stroke: #666;
                    stroke-width: 2px;
                }
                .tooltip {
                    position: absolute;
                    padding: 8px;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    pointer-events: none;
                    z-index: 1000;
                    direction: rtl;
                }
            </style>
            <script src="https://d3js.org/d3.v7.min.js"></script>
        </head>
        <body>
            <div id="graph"></div>
            <script>
                const data = DATA_PLACEHOLDER;
                
                let svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", "100%")
                    .attr("height", "100%");
                    
                let g = svg.append("g");
                
                // Add zoom behavior
                let zoom = d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on("zoom", (event) => {
                        g.attr("transform", event.transform);
                    });
                    
                svg.call(zoom);
                
                function updateGraph(data) {
                    // Clear existing graph
                    g.selectAll("*").remove();
                    
                    if (!data || !data.nodes || !data.links) return;
                    
                    let simulation = d3.forceSimulation(data.nodes)
                        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                        .force("charge", d3.forceManyBody().strength(-300))
                        .force("center", d3.forceCenter(window.innerWidth / 2, window.innerHeight / 2));
                    
                    // Draw links
                    let link = g.append("g")
                        .selectAll("path")
                        .data(data.links)
                        .enter().append("path")
                        .attr("class", "link")
                        .attr("marker-end", "url(#arrowhead)");
                    
                    // Add arrowhead marker
                    svg.append("defs").append("marker")
                        .attr("id", "arrowhead")
                        .attr("viewBox", "0 -5 10 10")
                        .attr("refX", 20)
                        .attr("refY", 0)
                        .attr("markerWidth", 6)
                        .attr("markerHeight", 6)
                        .attr("orient", "auto")
                        .append("path")
                        .attr("d", "M0,-5L10,0L0,5")
                        .attr("fill", "#666");
                    
                    // Draw nodes
                    let node = g.append("g")
                        .selectAll(".node")
                        .data(data.nodes)
                        .enter().append("g")
                        .attr("class", "node")
                        .call(d3.drag()
                            .on("start", dragstarted)
                            .on("drag", dragged)
                            .on("end", dragended));
                    
                    // Add circles to nodes
                    node.append("circle")
                        .attr("r", 30);
                    
                    // Add text to nodes
                    node.append("text")
                        .text(d => d.title);
                    
                    // Add tooltips
                    let tooltip = d3.select("body").append("div")
                        .attr("class", "tooltip")
                        .style("opacity", 0);
                    
                    node.on("mouseover", function(event, d) {
                        tooltip.transition()
                            .duration(200)
                            .style("opacity", .9);
                        tooltip.html(createTooltipContent(d))
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 10) + "px");
                    })
                    .on("mouseout", function(d) {
                        tooltip.transition()
                            .duration(500)
                            .style("opacity", 0);
                    })
                    .on("click", function(event, d) {
                        // Store selected node ID in localStorage
                        localStorage.setItem('selectedNodeId', d.id);
                    });
                    
                    simulation.on("tick", () => {
                        link.attr("d", d => {
                            let dx = d.target.x - d.source.x,
                                dy = d.target.y - d.source.y,
                                dr = Math.sqrt(dx * dx + dy * dy);
                            return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
                        });
                        
                        node.attr("transform", d => `translate(${d.x},${d.y})`);
                    });
                    
                    function dragstarted(event) {
                        if (!event.active) simulation.alphaTarget(0.3).restart();
                        event.subject.fx = event.subject.x;
                        event.subject.fy = event.subject.y;
                    }
                    
                    function dragged(event) {
                        event.subject.fx = event.x;
                        event.subject.fy = event.y;
                    }
                    
                    function dragended(event) {
                        if (!event.active) simulation.alphaTarget(0);
                        event.subject.fx = null;
                        event.subject.fy = null;
                    }
                }
                
                function createTooltipContent(note) {
                    let content = `<div>`;
                    content += `<strong>${note.title}</strong><br>`;
                    if (note.description) content += `${note.description}<br>`;
                    if (note.children && note.children.length) {
                        content += `Sub-tasks: ${note.children.length}<br>`;
                    }
                    content += `</div>`;
                    return content;
                }
                
                // Initialize graph with data
                updateGraph(data);
            </script>
        </body>
        </html>
        """
        
    def set_data(self, notes, relations=None):
        """Convert notes and relations to D3.js format and update the graph"""
        if not notes:
            return
            
        # Prepare data for D3.js
        nodes = []
        links = []
        
        # Add nodes
        for note in notes:
            nodes.append({
                'id': note['id'],
                'title': self.fix_hebrew_display_direction(note.get('title', '')),
                'description': self.fix_hebrew_display_direction(note.get('description', '')),
                'children': note.get('children', [])
            })
            
        # Add links from relations and children
        for note in notes:
            # Add relations
            if note.get('relations'):
                for rel_type, target_id in note['relations'].items():
                    links.append({
                        'source': note['id'],
                        'target': target_id,
                        'type': rel_type
                    })
            
            # Add children links
            if note.get('children'):
                for child_id in note['children']:
                    links.append({
                        'source': note['id'],
                        'target': child_id,
                        'type': 'child'
                    })
        
        # Create data object
        data = {'nodes': nodes, 'links': links}
        
        # Create temporary HTML file
        if self.html_file:
            try:
                os.unlink(self.html_file)
            except:
                pass
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            html_content = self.html_template.replace('DATA_PLACEHOLDER', json.dumps(data))
            f.write(html_content)
            self.html_file = f.name
            
    def open_graph(self, *args):
        """Open the graph visualization in the default web browser"""
        if self.html_file and os.path.exists(self.html_file):
            webbrowser.open('file://' + self.html_file)
            
    def fix_hebrew_display_direction(self, text):
        """Fix Hebrew text direction for display"""
        if text is None:
            return ""
        return get_display(str(text))
        
    def on_parent(self, instance, parent):
        """Clean up temporary files when widget is removed"""
        if not parent and self.html_file:
            try:
                os.unlink(self.html_file)
            except:
                pass 