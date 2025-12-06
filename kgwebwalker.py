# Jupyter Notebook Cell - Dual-View Knowledge Graph Explorer
# Author: Wolfgang Fahl / bitplan.com
# Loads navigation_steps.yaml and provides side-by-side iframe navigation
# WF 2025-11-16

# Install dependencies if needed
# !pip install pyyaml ipywidgets

import yaml
import ipywidgets as widgets
from IPython.display import display, HTML

# Load YAML configuration
with open('navigation_steps.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(f"✅ Loaded configuration")
print(f"📊 Node types: {len(config['node_types'])}")
print(f"🔗 Edge types: {len(config['edge_types'])}")
print(f"⚫ Nodes: {len(config['nodes'])}")
print(f"→ Edges: {len(config['edges'])}")
print(f"🚶 Walks: {len(config['walks'])}")

# Build walk sequences
def build_walk_sequence(walk_name):
    """Convert walk edges to node sequence"""
    walk = config['walks'][walk_name]
    nodes = []

    for step in walk['sequence']:
        edge_name = step['edge']
        edge = config['edges'][edge_name]

        # Add 'from' node if it's the first step
        if len(nodes) == 0:
            nodes.append(edge['from'])

        # Add 'to' node
        nodes.append(edge['to'])

    return nodes

# Interactive UI
class DualViewExplorer:
    def __init__(self, config):
        self.config = config
        self.walk_names = list(config['walks'].keys())
        self.current_walk = self.walk_names[0]
        self.current_step = 0
        self.node_sequence = build_walk_sequence(self.current_walk)

        # Create widgets
        self.walk_selector = widgets.Dropdown(
            options=[(config['walks'][w]['label'], w) for w in self.walk_names],
            description='Walk:',
            style={'description_width': 'initial'}
        )

        self.prev_button = widgets.Button(
            description='← Previous',
            button_style='info',
            disabled=True,
            icon='arrow-left'
        )

        self.next_button = widgets.Button(
            description='Next →',
            button_style='info',
            icon='arrow-right'
        )

        self.step_label = widgets.Label(value="")

        self.output = widgets.Output()

        # Event handlers
        self.walk_selector.observe(self.on_walk_change, names='value')
        self.prev_button.on_click(self.on_prev)
        self.next_button.on_click(self.on_next)

        # Layout
        self.nav_bar = widgets.HBox([
            self.prev_button,
            self.step_label,
            self.next_button
        ])
        self.controls = widgets.VBox([self.walk_selector, self.nav_bar])

    def on_walk_change(self, change):
        """Handle walk selection change"""
        self.current_walk = change['new']
        self.current_step = 0
        self.node_sequence = build_walk_sequence(self.current_walk)
        self.render_step()

    def render_step(self):
        """Render current step with side-by-side iframes"""
        with self.output:
            self.output.clear_output()

            node_name = self.node_sequence[self.current_step]
            node = self.config['nodes'][node_name]
            node_type = self.config['node_types'][node['type']]

            # Update navigation state
            self.prev_button.disabled = self.current_step == 0
            self.next_button.disabled = self.current_step == len(self.node_sequence) - 1
            self.step_label.value = f"Step {self.current_step + 1} of {len(self.node_sequence)}"

            # Build Wikidata URL or placeholder
            if node.get('wikidata_id'):
                wikidata_url = f"https://www.wikidata.org/wiki/{node['wikidata_id']}"
                wikidata_iframe = f'<iframe src="{wikidata_url}" width="100%" height="600" frameborder="1"></iframe>'
            else:
                wikidata_iframe = f'''
                <div style="padding: 40px; background: #fee; border: 2px solid #e74c3c; height: 600px; display: flex; align-items: center; justify-content: center;">
                    <div style="text-align: center;">
                        <h2>⚠️ No Wikidata Entry</h2>
                        <p style="font-size: 16px;"><strong>{node['label']}</strong></p>
                        <p>This entity exists on the web but not yet in Wikidata.</p>
                        <p style="margin-top: 20px;"><em>Sync challenge: Create entry to complete the knowledge graph</em></p>
                    </div>
                </div>
                '''

            # Build HTML
            html = f"""
            <style>
                .explorer-container {{
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }}
                .node-header {{
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 15px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                }}
                .dual-view {{
                    display: flex;
                    gap: 20px;
                }}
                .view-pane {{
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }}
                .pane-header {{
                    padding: 10px;
                    font-weight: bold;
                    text-align: center;
                    color: white;
                    border-radius: 4px 4px 0 0;
                }}
                .kg-header {{ background: #27ae60; }}
                .web-header {{ background: #3498db; }}
                .pane-subtitle {{
                    padding: 8px;
                    background: #ecf0f1;
                    text-align: center;
                    font-size: 14px;
                    border: 1px solid #ccc;
                    border-top: none;
                }}
            </style>

            <div class="explorer-container">
                <div class="node-header">
                    {node_type['icon']} {node['label']}
                </div>

                <div class="dual-view">
                    <div class="view-pane">
                        <div class="pane-header kg-header">🔗 Knowledge Graph (Wikidata)</div>
                        <div class="pane-subtitle">{node.get('wikidata_id', 'Not created yet')}</div>
                        {wikidata_iframe}
                    </div>

                    <div class="view-pane">
                        <div class="pane-header web-header">🌐 Traditional Web (HTML)</div>
                        <div class="pane-subtitle">{node['web_url']}</div>
                        <iframe src="{node['web_url']}" width="100%" height="600" frameborder="1"></iframe>
                    </div>
                </div>
            </div>
            """

            display(HTML(html))

    def on_prev(self, b):
        if self.current_step > 0:
            self.current_step -= 1
            self.render_step()

    def on_next(self, b):
        if self.current_step < len(self.node_sequence) - 1:
            self.current_step += 1
            self.render_step()

    def display(self):
        display(self.controls)
        display(self.output)
        self.render_step()

# Create and display explorer
explorer = DualViewExplorer(config)
explorer.display()
