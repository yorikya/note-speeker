from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.label import Label
import os
from bidi.algorithm import get_display
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

class NoteGraphWidget(Widget):
    def __init__(self, fetch_note_by_id=None, get_language=None, fix_hebrew_display_direction=None, **kwargs):
        super().__init__(**kwargs)
        self.notes = []
        self.relations = []
        self.labels = []
        self.node_positions = []
        self.fetch_note_by_id = fetch_note_by_id  # callback to fetch note data by id
        self.get_language = get_language  # callback to get current language
        self.fix_hebrew_display_direction = fix_hebrew_display_direction  # callback for Hebrew direction
        self.tooltip_label = None
        self.bind(size=self._on_resize, pos=self._on_resize)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def set_data(self, notes, relations):
        self.notes = notes
        self.relations = relations
        self.draw_graph()

    def _on_resize(self, *args):
        # Redraw and reposition nodes/labels on resize
        self.draw_graph()

    def draw_graph(self):
        self.canvas.clear()
        # Remove old labels
        for label in getattr(self, 'labels', []):
            self.remove_widget(label)
        if self.tooltip_label:
            self.remove_widget(self.tooltip_label)
            self.tooltip_label = None
        self.labels = []
        self.node_positions = []
        if not self.notes:
            return
        # Layout: spread nodes horizontally, centered vertically, with margin
        margin_x = dp(60)
        margin_y = dp(40)
        node_radius = dp(60)  # Increased size
        area_width = max(self.width - 2 * margin_x, dp(100))
        area_height = max(self.height - 2 * margin_y, dp(100))
        n = len(self.notes)
        if n == 1:
            positions = [(self.x + self.width / 2, self.y + self.height / 2)]
        else:
            # Spread nodes horizontally, avoid bottom overlap
            step = area_width / (n - 1) if n > 1 else 0
            positions = [
                (self.x + margin_x + i * step, self.y + self.height / 2)
                for i in range(n)
            ]
        for note, pos in zip(self.notes, positions):
            note['pos'] = pos
            self.node_positions.append((pos, note))
        with self.canvas:
            # Draw edges
            Color(0.5, 0.7, 1, 1)
            for rel in self.relations:
                from_note = next((n for n in self.notes if n['id'] == rel[0]), None)
                to_note = next((n for n in self.notes if n['id'] == rel[1]), None)
                if from_note and to_note:
                    Line(points=[*from_note['pos'], *to_note['pos']], width=2)
            for note in self.notes:
                x, y = note['pos']
                # Drop shadow
                Color(0, 0, 0, 0.25)
                Ellipse(pos=(x - node_radius + 4, y - node_radius - 4), size=(node_radius * 2, node_radius * 2))
                # Node fill
                Color(0.18, 0.45, 0.85, 1)
                Ellipse(pos=(x - node_radius, y - node_radius), size=(node_radius * 2, node_radius * 2))
                # Node border
                Color(1, 1, 1, 1)
                Line(circle=(x, y, node_radius), width=3)
        # Add labels as widgets for better font rendering
        font_path = 'app/fonts/Alef-Regular.ttf'
        lang = self.get_language() if self.get_language else 'en-US'
        for note in self.notes:
            x, y = note['pos']
            title = note.get('title', '')
            # Truncate to 20 chars
            if len(title) > 20:
                title = title[:20] + '...'
            # Fix Hebrew direction if needed
            if lang.startswith('he') and self.fix_hebrew_display_direction:
                title = self.fix_hebrew_display_direction(title)
                # Reverse the order of words (not letters)
                title = ' '.join(title.split()[::-1])
            label = Label(text=title,
                          font_size='32sp',
                          color=(1, 1, 1, 1),
                          bold=True,
                          font_name=font_path if os.path.exists(font_path) else None,
                          size_hint=(None, None),
                          size=(node_radius * 2, node_radius * 1.2),
                          halign='center',
                          valign='middle',
                          pos=(x - node_radius, y - node_radius / 2))
            label.text_size = (node_radius * 2, node_radius * 1.2)
            self.add_widget(label)
            self.labels.append(label)

    def on_touch_down(self, touch):
        # Check if a node was clicked
        node_radius = dp(36)
        for pos, note in self.node_positions:
            x, y = pos
            if (x - touch.x) ** 2 + (y - touch.y) ** 2 <= node_radius ** 2:
                # Node was clicked
                if 'children' in note and note['children'] and self.fetch_note_by_id:
                    # Fetch children notes and show them
                    children_notes = [self.fetch_note_by_id(child_id) for child_id in note['children']]
                    # Remove None (if any child not found)
                    children_notes = [n for n in children_notes if n]
                    # Create relations from parent to each child
                    relations = [(note['id'], child['id']) for child in children_notes]
                    # Show parent and children
                    self.set_data([note] + children_notes, relations)
                    return True
        return super().on_touch_down(touch)

    def fix_hebrew_display_direction(self, text):
        """Fix Hebrew text direction for display in UI widgets"""
        if text is None:
            return ""  # Return empty string for None values
        from bidi.algorithm import get_display
        return get_display(str(text))

    def on_mouse_pos(self, window, pos):
        node_radius = dp(36)
        for node_pos, note in self.node_positions:
            x, y = node_pos
            if (x - pos[0]) ** 2 + (y - pos[1]) ** 2 <= node_radius ** 2:
                if not self.tooltip_label:
                    # Fix Hebrew text direction for each field
                    info_items = []
                    for k, v in note.items():
                        if k != 'pos':
                            # Fix both key and value, handle None values
                            fixed_key = self.fix_hebrew_display_direction(k) if k is not None else ""
                            fixed_value = self.fix_hebrew_display_direction(v) if v is not None else ""
                            if fixed_key or fixed_value:  # Only add if either has content
                                info_items.append(f"{fixed_key}: {fixed_value}")
                    info = '\n'.join(info_items)
                    
                    from kivy.uix.floatlayout import FloatLayout
                    from kivy.graphics import Color, RoundedRectangle
                    self.tooltip_label = FloatLayout(size_hint=(None, None), size=(dp(300), dp(120)))
                    
                    with self.tooltip_label.canvas.before:
                        Color(0, 0, 0, 0.8)  # Semi-transparent black
                        self.rect = RoundedRectangle(pos=self.tooltip_label.pos, size=self.tooltip_label.size, radius=[dp(10)])
                    
                    from kivy.uix.label import Label
                    import os
                    
                    content = Label(
                        text=info,
                        color=(1, 1, 1, 1),  # White text
                        size_hint=(None, None),
                        size=self.tooltip_label.size,
                        halign='right',  # Right-aligned for Hebrew
                        valign='middle',
                        font_name='app/fonts/Alef-Regular.ttf' if os.path.exists('app/fonts/Alef-Regular.ttf') else None,
                        font_size='16sp',
                        padding=(dp(10), dp(10))
                    )
                    content.text_size = content.size  # Enable text wrapping
                    self.tooltip_label.add_widget(content)
                    
                    # Convert widget coordinates to window coordinates
                    win_x, win_y = self.to_window(x, y)
                    
                    # Position tooltip to the right of the node
                    tooltip_x = win_x + node_radius + dp(10)
                    tooltip_y = win_y - self.tooltip_label.height / 2
                    
                    # Adjust if tooltip would go off screen
                    if tooltip_x + self.tooltip_label.width > Window.width:
                        tooltip_x = win_x - node_radius - dp(10) - self.tooltip_label.width
                    if tooltip_y < 0:
                        tooltip_y = 0
                    elif tooltip_y + self.tooltip_label.height > Window.height:
                        tooltip_y = Window.height - self.tooltip_label.height
                    
                    self.tooltip_label.pos = (tooltip_x, tooltip_y)
                    Window.add_widget(self.tooltip_label)
                return
        if self.tooltip_label:
            Window.remove_widget(self.tooltip_label)
            self.tooltip_label = None

    def on_parent(self, instance, parent):
        # Register mouse motion event when added to parent
        if parent:
            from kivy.core.window import Window
            Window.bind(mouse_pos=self._on_mouse_pos_wrapper)
        else:
            from kivy.core.window import Window
            Window.unbind(mouse_pos=self._on_mouse_pos_wrapper)
            if self.tooltip_label:
                Window.remove_widget(self.tooltip_label)
                self.tooltip_label = None

    def _on_mouse_pos_wrapper(self, window, pos):
        # Convert window coords to local
        if not self.get_root_window():
            return
        local = self.to_widget(*pos)
        self.on_mouse_pos(window, local) 