"""A widget to display a graph of notes."""
import math
import arabic_reshaper
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.core.window import Window
from bidi.algorithm import get_display
from kivy.uix.widget import Widget
from kivy.metrics import dp


class NoteNode(RelativeLayout):
    """Widget for a single node in the graph."""
    def __init__(self, note_data, **kwargs):
        super().__init__(**kwargs)
        self.note_data = note_data
        self.size_hint = (None, None)
        self.size = (100, 100) # Circle: width and height should be equal

        title = self.note_data.get('title', 'No Title')
        
        # Manually add newlines to control wrapping, then apply bidi.
        # This ensures correct display inside the constrained circle.
        title_with_newlines = title.replace(' ', '\n')
        reshaped_text = arabic_reshaper.reshape(title_with_newlines)
        display_title = get_display(reshaped_text)

        self.label = Label(
            text=display_title,
            size_hint=(None, None),
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
            font_name='app/fonts/Alef-Regular.ttf',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.label.bind(
            width=lambda *x: self.label.setter('text_size')(self.label, (self.width - dp(20), None)),
            texture_size=lambda *x: self.label.setter('size')(self.label, x[1])
        )
        self.add_widget(self.label)

        with self.canvas.before:
            Color(0.2, 0.6, 0.9, 1)
            self.rect = Ellipse(size=self.size, pos=(0,0))
            Color(0.5, 0.7, 1, 1)  # Border color
            self.border = Line(ellipse=(0, 0, self.width, self.height), width=1.5)

        self.bind(size=self.update_graphics)

    def update_graphics(self, *args):
        self.rect.size = self.size
        self.border.ellipse = (0, 0, self.width, self.height)


class Tooltip(Label):
    """Tooltip label."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.color = (1, 1, 1, 1)
        self.font_name = 'app/fonts/Alef-Regular.ttf'  # Font for Hebrew
        with self.canvas.before:
            Color(0, 0, 0, 0.8)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_text(self, text):
        reshaped_text = arabic_reshaper.reshape(text)
        display_text = get_display(reshaped_text)
        self.text = display_text
        self.texture_update()
        if self.texture_size:
            self.size = (self.texture_size[0] + dp(20), self.texture_size[1] + dp(10))


class NoteGraphWidget(RelativeLayout):
    """A widget for visualizing notes as a graph."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nodes = {}
        self.links = []
        self.node_widgets = {}
        self._tooltip = None
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.bind(size=self.draw_graph, pos=self.draw_graph)
        
    def set_data(self, notes, relations=None):
        """Set the data for the graph."""
        self.nodes.clear()
        self.links.clear()

        if not notes:
            self.draw_graph()
            return
            
        for note in notes:
            self.nodes[note['id']] = note

        if relations:
            self.links = relations
        
        self.draw_graph()

    def draw_graph(self, *args):
        """Draw the graph on the widget's canvas."""
        self.clear_widgets()
        self.node_widgets.clear()
        
        if not self.nodes:
            return

        center_x = self.width / 2
        center_y = self.height / 2
        radius = min(self.width, self.height) / 3 if min(self.width, self.height) > 0 else 100
            
        angle_step = (2 * math.pi) / len(self.nodes) if len(self.nodes) > 0 else 0

        positions = {}
        node_ids = list(self.nodes.keys())
        for i, node_id in enumerate(node_ids):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[node_id] = (x, y)

        # Create a widget to draw links on, and add it first so it's in the background
        links_widget = Widget()
        with links_widget.canvas:
            Color(0.5, 0.5, 0.5, 1)
            for link in self.links:
                source_pos = positions.get(link['source'])
                target_pos = positions.get(link['target'])
                if source_pos and target_pos:
                    Line(points=[source_pos[0], source_pos[1],
                                target_pos[0], target_pos[1]], width=1.5)
        self.add_widget(links_widget)

        for node_id, pos in positions.items():
            node_widget = NoteNode(
                note_data=self.nodes[node_id],
                pos=(pos[0] - 50, pos[1] - 50) # Center the circle
            )
            self.add_widget(node_widget)
            self.node_widgets[node_id] = node_widget

    def on_mouse_pos(self, *args):
        """Handle mouse movement for tooltips."""
        pos = args[1]
        
        if self._tooltip and self._tooltip.parent:
            self.remove_widget(self._tooltip)
        self._tooltip = None

        if self.parent: # Ensure the widget is attached to a parent
            widget_pos = self.to_widget(*pos, relative=True)
            for node_id, node_widget in self.node_widgets.items():
                if node_widget.collide_point(*widget_pos):
                    node_data = self.nodes.get(node_id, {})
                    
                    title = node_data.get('title', '')
                    desc = node_data.get('description', '')
                    tooltip_text = f"Title: {title}"
                    if desc:
                        tooltip_text += f"\nDescription: {desc}"
                    
                    self._tooltip = Tooltip(pos=widget_pos)
                    self.add_widget(self._tooltip)
                    self._tooltip.set_text(tooltip_text)
                    break