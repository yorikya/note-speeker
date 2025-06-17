from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from app.widgets import LanguageDropdown


class SettingsScreen(Screen):
    """Settings screen with language selection and other options"""
    
    def __init__(self, app_instance, **kwargs):
        print("DEBUG: SettingsScreen.__init__() called")
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'settings'
        print(f"DEBUG: SettingsScreen name set to: {self.name}")
        
        # Set background gradient
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            # Modern gradient background (dark blue to dark gray)
            Color(0.1, 0.15, 0.25, 1)  # Dark blue-gray
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_bg, pos=self._update_bg)
        
        try:
            self.setup_ui()
            print("DEBUG: SettingsScreen UI setup completed")
        except Exception as e:
            print(f"DEBUG: Error in SettingsScreen setup_ui: {e}")
            raise
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def setup_ui(self):
        """Set up the settings screen UI"""
        main_layout = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(25))
        
        # Header with modern styling
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70))
        
        back_btn = Button(
            text='← Back',
            size_hint=(None, 1),
            width=dp(120),
            font_size='18sp',
            background_color=(0.2, 0.6, 1.0, 1),  # Modern blue
            color=(1, 1, 1, 1),
            bold=True
        )
        back_btn.bind(on_press=lambda x: self.app_instance.show_home_screen())
        
        title = Label(
            text='Settings',
            font_size='28sp',
            bold=True,
            color=(1, 1, 1, 1),  # White text
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        
        # Create scrollable content with card-like sections
        scroll = ScrollView()
        content = BoxLayout(
            orientation='vertical', 
            spacing=dp(25),
            size_hint_y=None,
            padding=[0, dp(15), 0, dp(15)]
        )
        content.bind(minimum_height=content.setter('height'))
        
        # Language selection section (card style)
        lang_card = self.create_card_section()
        self.language_dropdown = LanguageDropdown(
            self.app_instance.speech_service,
            self.app_instance.config_service
        )
        # Update dropdown styling
        self.style_language_dropdown()
        lang_card.add_widget(self.language_dropdown)
        content.add_widget(lang_card)
        
        # Silence timeout section (card style)  
        silence_card = self.create_card_section()
        silence_section = self.create_silence_timeout_section()
        silence_card.add_widget(silence_section)
        content.add_widget(silence_card)
        
        # Recording timeout section (card style)
        recording_card = self.create_card_section()
        recording_section = self.create_recording_timeout_section()
        recording_card.add_widget(recording_section)
        content.add_widget(recording_card)
        
        # Config info section (card style)
        config_card = self.create_card_section()
        config_info = self.create_config_info()
        config_card.add_widget(config_info)
        content.add_widget(config_card)
        
        # Reset settings section (card style)
        reset_card = self.create_card_section()
        reset_section = self.create_reset_section()
        reset_card.add_widget(reset_section)
        content.add_widget(reset_card)
        
        scroll.add_widget(content)
        
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)
    
    def create_card_section(self):
        """Create a card-like container for sections"""
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(20),
            spacing=dp(10)
        )
        
        # Add card background with rounded corners effect
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.25, 0.35, 0.9)  # Semi-transparent dark card
            card.bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[15])
            card.bind(size=lambda instance, value: setattr(card.bg, 'size', value))
            card.bind(pos=lambda instance, value: setattr(card.bg, 'pos', value))
        
        # Calculate height dynamically
        card.bind(minimum_height=card.setter('height'))
        
        return card
    
    def style_language_dropdown(self):
        """Apply modern styling to language dropdown"""
        if hasattr(self.language_dropdown, 'main_button'):
            self.language_dropdown.main_button.background_color = (0.15, 0.2, 0.3, 1)
            self.language_dropdown.main_button.color = (1, 1, 1, 1)
            self.language_dropdown.main_button.font_size = '16sp'
            self.language_dropdown.main_button.bold = True
    
    def create_silence_timeout_section(self):
        """Create silence timeout setting section with modern styling"""
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(15)
        )
        
        # Section title
        title_label = Label(
            text='🔇 Auto-Stop on Silence',
            size_hint_y=None,
            height=dp(35),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True,
            halign='left'
        )
        title_label.text_size = (None, None)
        
        # Current value display with modern styling
        current_timeout = self.app_instance.config_service.get_silence_timeout()
        self.timeout_label = Label(
            text=f'Stop after {current_timeout} seconds of silence',
            size_hint_y=None,
            height=dp(30),
            color=(0.8, 0.9, 1.0, 1),  # Light blue
            font_size='16sp',
            halign='left'
        )
        self.timeout_label.text_size = (None, None)
        
        # Modern slider with custom styling (1-60 seconds range)
        self.timeout_slider = Slider(
            min=1,
            max=60,
            value=current_timeout,
            step=1,
            size_hint_y=None,
            height=dp(40)
        )
        # Custom slider colors
        self.timeout_slider.cursor_image = ''  # Remove default cursor
        self.timeout_slider.background_width = dp(4)
        self.timeout_slider.bind(value=self.on_timeout_change)
        
        section.add_widget(title_label)
        section.add_widget(self.timeout_label)
        section.add_widget(self.timeout_slider)
        
        return section
    
    def create_recording_timeout_section(self):
        """Create recording timeout setting section with modern styling"""
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(15)
        )
        
        # Section title
        title_label = Label(
            text='⏱️ Max Recording Duration',
            size_hint_y=None,
            height=dp(35),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True,
            halign='left'
        )
        title_label.text_size = (None, None)
        
        # Current value display with modern styling
        current_recording_timeout = self.app_instance.config_service.get_recording_timeout()
        minutes = current_recording_timeout // 60
        self.recording_timeout_label = Label(
            text=f'Auto-stop after {minutes} minutes',
            size_hint_y=None,
            height=dp(30),
            color=(0.8, 0.9, 1.0, 1),  # Light blue
            font_size='16sp',
            halign='left'
        )
        self.recording_timeout_label.text_size = (None, None)
        
        # Modern slider with custom styling (1-30 minutes range)
        self.recording_timeout_slider = Slider(
            min=1,
            max=30,
            value=minutes,
            step=1,
            size_hint_y=None,
            height=dp(40)
        )
        # Custom slider colors
        self.recording_timeout_slider.cursor_image = ''  # Remove default cursor
        self.recording_timeout_slider.background_width = dp(4)
        self.recording_timeout_slider.bind(value=self.on_recording_timeout_change)
        
        section.add_widget(title_label)
        section.add_widget(self.recording_timeout_label)
        section.add_widget(self.recording_timeout_slider)
        
        return section
    
    def create_config_info(self):
        """Create configuration file info section with modern styling"""
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(90),
            spacing=dp(10)
        )
        
        title_label = Label(
            text='💾 Configuration',
            size_hint_y=None,
            height=dp(35),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True,
            halign='left'
        )
        title_label.text_size = (None, None)
        
        config_path = self.app_instance.config_service.config_file
        info_label = Label(
            text=f'Settings saved to:\n{config_path}',
            size_hint_y=None,
            height=dp(45),
            color=(0.7, 0.8, 0.9, 1),  # Light gray-blue
            font_size='14sp',
            halign='left',
            valign='top'
        )
        info_label.text_size = (None, None)
        
        section.add_widget(title_label)
        section.add_widget(info_label)
        
        return section
    
    def create_reset_section(self):
        """Create reset settings section with modern styling"""
        section = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(90),
            spacing=dp(15)
        )
        
        title_label = Label(
            text='🔄 Reset Settings',
            size_hint_y=None,
            height=dp(35),
            color=(1, 1, 1, 1),
            font_size='20sp',
            bold=True,
            halign='left'
        )
        title_label.text_size = (None, None)
        
        reset_btn = Button(
            text='Reset to Defaults',
            size_hint_y=None,
            height=dp(45),
            font_size='16sp',
            background_color=(0.9, 0.3, 0.3, 1),  # Modern red
            color=(1, 1, 1, 1),
            bold=True
        )
        reset_btn.bind(on_press=self.reset_settings)
        
        section.add_widget(title_label)
        section.add_widget(reset_btn)
        
        return section
    
    def on_timeout_change(self, instance, value):
        """Handle silence timeout slider change"""
        timeout = int(value)
        self.timeout_label.text = f'Stop after {timeout} seconds of silence'
        self.app_instance.config_service.set_silence_timeout(timeout)
    
    def on_recording_timeout_change(self, instance, value):
        """Handle recording timeout slider change"""
        minutes = int(value)
        seconds = minutes * 60
        self.recording_timeout_label.text = f'Auto-stop after {minutes} minutes'
        self.app_instance.config_service.set_recording_timeout(seconds)
    
    def reset_settings(self, instance):
        """Reset all settings to defaults"""
        # Reset to defaults
        self.app_instance.config_service.set_language('en-US')
        self.app_instance.config_service.set_silence_timeout(5)
        self.app_instance.config_service.set_recording_timeout(600)  # 10 minutes
        
        # Update UI
        self.language_dropdown.refresh_selection()
        self.timeout_slider.value = 5
        self.timeout_label.text = 'Stop after 5 seconds of silence'
        self.recording_timeout_slider.value = 10
        self.recording_timeout_label.text = 'Auto-stop after 10 minutes'
        
        print("Settings reset to defaults")
    
    def on_enter(self):
        """Called when entering the settings screen"""
        # Refresh the language dropdown to show current setting
        if hasattr(self, 'language_dropdown'):
            self.language_dropdown.refresh_selection() 