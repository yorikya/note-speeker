from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.metrics import dp


class SideMenu(BoxLayout):
    """Modern animated side menu widget"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(280)  # Slightly wider for modern look
        self.x = -self.width  # Start hidden
        
        # Modern gradient background
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle, Line
            # Dark gradient background
            Color(0.15, 0.2, 0.3, 0.95)  # Semi-transparent dark blue
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            
            # Add subtle border
            Color(0.3, 0.4, 0.6, 0.8)  # Light blue border
            self.border_line = Line(rectangle=(self.x + self.width - 2, self.y, 2, self.height), width=2)
            
            self.bind(size=self._update_graphics, pos=self._update_graphics)
        
        self.setup_ui()
    
    def _update_graphics(self, *args):
        """Update background graphics when size/position changes"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rectangle = (self.x + self.width - 2, self.y, 2, self.height)
    
    def setup_ui(self):
        """Set up the side menu UI with modern styling"""
        # Header section with app branding
        header = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(10),
            padding=[dp(25), dp(30), dp(25), dp(20)]
        )
        
        # App title with modern typography
        title = Label(
            text='🎙️ Note Speaker',
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),  # White text
            halign='left',
        )
        title.text_size = (self.width - dp(50), None)
        
        # Subtitle with current language
        current_lang = self.app_instance.config_service.get_language()
        lang_name = self.app_instance.speech_service.LANGUAGES.get(current_lang, 'Unknown')
        subtitle = Label(
            text=f'Language: {lang_name}',
            font_size='14sp',
            color=(0.7, 0.8, 0.9, 1),  # Light blue-gray
            halign='left',
            italic=True
        )
        subtitle.text_size = (self.width - dp(50), None)
        
        header.add_widget(title)
        header.add_widget(subtitle)
        
        # Navigation section
        nav_section = BoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=[dp(15), dp(20), dp(15), dp(20)]
        )
        
        # Navigation buttons with modern styling
        nav_buttons = [
            ('🏠', 'Home', self.go_to_home),
            ('⚙️', 'Settings', self.go_to_settings),
            ('📝', 'Notes', self.go_to_notes),
            ('ℹ️', 'About', self.go_to_about)
        ]
        
        for icon, text, callback in nav_buttons:
            btn = self.create_nav_button(icon, text, callback)
            nav_section.add_widget(btn)
        
        # Footer section
        footer = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(25), dp(20), dp(25), dp(30)]
        )
        
        # Version info
        version_label = Label(
            text='v1.0.0',
            font_size='12sp',
            color=(0.5, 0.6, 0.7, 1),  # Muted gray
            halign='left'
        )
        version_label.text_size = (self.width - dp(50), None)
        
        footer.add_widget(version_label)
        
        # Add sections to main layout
        self.add_widget(header)
        self.add_widget(nav_section)
        self.add_widget(footer)
    
    def create_nav_button(self, icon, text, callback):
        """Create a navigation button with modern styling"""
        btn = Button(
            text=f'{icon}  {text}',
            size_hint_y=None,
            height=dp(55),
            font_size='16sp',
            halign='left',
            valign='center',
            background_color=(0, 0, 0, 0),  # Transparent background
            color=(0.9, 0.95, 1.0, 1),  # Light white
            bold=True
        )
        
        # Set text alignment
        btn.text_size = (self.width - dp(60), None)
        
        # Add custom background with hover effects
        with btn.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            btn.bg_color = Color(0.2, 0.3, 0.4, 0)  # Start transparent
            btn.bg = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[10])
            btn.bind(size=lambda instance, value: setattr(btn.bg, 'size', value))
            btn.bind(pos=lambda instance, value: setattr(btn.bg, 'pos', value))
        
        # Bind events for hover effects and navigation
        btn.bind(state=self.on_button_state)
        btn.bind(on_press=lambda x: self.handle_nav_press(callback))
        
        return btn
    
    def on_button_state(self, button, state):
        """Handle button state changes for hover effects"""
        if state == 'down':
            # Highlight on press
            button.bg_color.rgba = (0.2, 0.6, 1.0, 0.3)  # Blue highlight
            button.color = (1, 1, 1, 1)  # Full white
        else:
            # Normal state
            button.bg_color.rgba = (0.2, 0.3, 0.4, 0)  # Transparent
            button.color = (0.9, 0.95, 1.0, 1)  # Light white
    
    def handle_nav_press(self, callback):
        """Handle navigation button press"""
        print(f"DEBUG: SideMenu nav button pressed, calling callback: {callback.__name__}")
        # Hide menu first
        self.hide()
        # Then execute callback
        callback()
    
    def show(self):
        """Show the side menu with smooth animation"""
        print("DEBUG: SideMenu.show() called")
        anim = Animation(x=0, duration=0.3, transition='out_quart')
        anim.start(self)
    
    def hide(self):
        """Hide the side menu with smooth animation"""
        print("DEBUG: SideMenu.hide() called")
        anim = Animation(x=-self.width, duration=0.3, transition='out_quart')
        anim.start(self)
    
    def is_visible(self):
        """Check if menu is currently visible"""
        return self.x >= -10  # Account for animation tolerance
    
    # Navigation callbacks
    def go_to_home(self):
        """Navigate to home screen"""
        print("DEBUG: Navigating to home screen")
        self.app_instance.show_home_screen()
    
    def go_to_settings(self):
        """Navigate to settings screen"""
        print("DEBUG: Navigating to settings screen")
        self.app_instance.show_settings_screen()
    
    def go_to_notes(self):
        """Navigate to notes screen"""
        print("DEBUG: Navigating to notes screen")
        self.app_instance.show_notes_screen()
    
    def go_to_about(self):
        """Navigate to about screen"""
        print("DEBUG: Navigating to about screen")
        self.app_instance.show_about_screen()
    
    def refresh_language_display(self):
        """Refresh the language display in the subtitle"""
        if hasattr(self, 'children') and self.children:
            # Find the header section and update subtitle
            header = self.children[-1]  # Header is the first added (last in children)
            if hasattr(header, 'children') and len(header.children) > 1:
                subtitle = header.children[0]  # Subtitle is second added (first in children)
                current_lang = self.app_instance.config_service.get_language()
                lang_name = self.app_instance.speech_service.LANGUAGES.get(current_lang, 'Unknown')
                subtitle.text = f'Language: {lang_name}' 