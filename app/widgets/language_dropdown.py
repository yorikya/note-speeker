from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp


class LanguageDropdown(BoxLayout):
    """A custom dropdown widget for language selection"""
    
    def __init__(self, speech_service, config_service, **kwargs):
        super().__init__(**kwargs)
        self.speech_service = speech_service
        self.config_service = config_service
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.spacing = dp(10)
        
        self.setup_ui()
        self.refresh_selection()
    
    def setup_ui(self):
        """Set up the dropdown UI with modern styling"""
        # Section title with emoji and modern styling
        title = Label(
            text='🌐 Speech Recognition Language',
            size_hint_y=None,
            height=dp(35),
            color=(1, 1, 1, 1),  # White text
            font_size='20sp',
            bold=True,
            halign='left'
        )
        title.text_size = (None, None)
        
        # Create dropdown menu with modern styling
        self.dropdown = DropDown()
        
        # Populate dropdown with languages
        for lang_code, lang_name in self.speech_service.LANGUAGES.items():
            btn = Button(
                text=lang_name,
                size_hint_y=None,
                height=dp(50),
                font_size='15sp',
                background_color=(0.25, 0.3, 0.4, 1),  # Dark blue-gray
                color=(1, 1, 1, 1),  # White text
                halign='left',
                valign='center'
            )
            # Style text alignment
            btn.text_size = (None, None)
            btn.bind(on_release=lambda btn, code=lang_code: self.select_language(code))
            
            # Add hover effect
            btn.bind(state=self.on_button_state)
            
            self.dropdown.add_widget(btn)
        
        # Main button with modern styling
        self.main_button = Button(
            text='Select Language',
            size_hint_y=None,
            height=dp(50),
            font_size='16sp',
            background_color=(0.15, 0.2, 0.3, 1),  # Dark blue
            color=(1, 1, 1, 1),  # White text
            bold=True,
            halign='left'
        )
        self.main_button.text_size = (self.main_button.width - dp(40), None)
        self.main_button.bind(width=self.update_button_text_size)
        
        # Add dropdown arrow indicator
        with self.main_button.canvas.after:
            from kivy.graphics import Color, Line
            Color(0.8, 0.9, 1.0, 1)  # Light blue arrow
            # Draw dropdown arrow
            arrow_points = []
            def draw_arrow(instance, value):
                instance.canvas.after.clear()
                with instance.canvas.after:
                    Color(0.8, 0.9, 1.0, 1)
                    # Arrow pointing down
                    x = instance.right - dp(25)
                    y = instance.center_y
                    Line(points=[x-dp(8), y+dp(4), x, y-dp(4), x+dp(8), y+dp(4)], width=2)
            
            self.main_button.bind(pos=draw_arrow, size=draw_arrow)
            draw_arrow(self.main_button, None)
        
        # Bind dropdown to main button
        self.main_button.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self.main_button, 'text', x))
        
        self.add_widget(title)
        self.add_widget(self.main_button)
    
    def on_button_state(self, button, state):
        """Handle button hover effects"""
        if state == 'down':
            button.background_color = (0.35, 0.4, 0.5, 1)  # Lighter on press
        else:
            button.background_color = (0.25, 0.3, 0.4, 1)  # Original color
    
    def update_button_text_size(self, instance, width):
        """Update text size when button width changes"""
        instance.text_size = (width - dp(40), None)
    
    def select_language(self, lang_code):
        """Handle language selection"""
        print(f"DEBUG: Language selected: {lang_code}")
        
        # Update the config
        self.config_service.set_language(lang_code)
        
        # Update the speech service language
        self.speech_service.set_language(lang_code)
        
        # Update button text - simple display since we only have 2 languages
        lang_name = self.speech_service.LANGUAGES[lang_code]
        self.main_button.text = lang_name
        
        # Close dropdown
        self.dropdown.dismiss()
        
        print(f"DEBUG: Language changed to: {lang_name}")
        print(f"DEBUG: Speech service updated to: {lang_code}")
        
        # Refresh main screen if possible to update fonts and display
        try:
            # Get the app instance to access screens
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, 'main_screen'):
                app.main_screen.update_notes_font()
                app.main_screen.refresh_notes_display()
                print("DEBUG: Main screen font and display refreshed")
        except Exception as e:
            print(f"DEBUG: Could not refresh main screen: {e}")
    
    def refresh_selection(self):
        """Refresh the dropdown to show current language"""
        current_lang = self.config_service.get_language()
        if current_lang in self.speech_service.LANGUAGES:
            lang_name = self.speech_service.LANGUAGES[current_lang]
            self.main_button.text = lang_name
            print(f"DEBUG: Dropdown refreshed to show: {lang_name}")
        else:
            self.main_button.text = 'Select Language' 