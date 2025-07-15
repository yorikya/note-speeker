# -*- coding: utf-8 -*-
import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager
from kivy.animation import Animation
from kivy.core.text import LabelBase
import platform
from kivy.core.window import Window
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivy.config import Config
import os
import sys
import types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.modules['grpc'] = types.ModuleType('grpc')
os.environ["KIVY_LOG_DIR"] = "/sdcard/"

# Import our custom modules
from app.widgets import SideMenu
from app.screens import MainScreen, SettingsScreen, NotesScreen, HelpScreen
from app.services import SpeechService, ConfigService
from app.services.nlp_service import NLPService
from app.services.log_service import LogService
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import traceback

# Kivy requires minimum version
kivy.require('2.0.0')

# Set window size constraints
Window.minimum_width = 800
Window.minimum_height = 600
Window.size = (1200, 800)

# Register Hebrew-supporting fonts
def register_hebrew_fonts():
    """Register fonts that support Hebrew characters"""
    current_platform = platform.system()
    
    try:
        if current_platform == "Darwin":  # macOS
            # Use macOS Hebrew-specific fonts
            font_paths = [
                "/System/Library/Fonts/SFHebrew.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/System/Library/Fonts/SFHebrewRounded.ttf",
                "/System/Library/Fonts/Arial.ttf", 
                "/System/Library/Fonts/Helvetica.ttc"
            ]
        elif current_platform == "Windows":
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf"
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/arial.ttf"
            ]
        
        for font_path in font_paths:
            try:
                import os
                if os.path.exists(font_path):
                    LabelBase.register(name="HebrewFont", fn_regular=font_path)
                    print(f"Registered Hebrew font: {font_path}")
                    return True  # Success, stop trying other fonts
            except Exception as e:
                print(f"Failed to register font {font_path}: {e}")
                continue
        
        print("No Hebrew fonts found, using default")
        return False
            
    except Exception as e:
        print(f"Error registering Hebrew fonts: {e}")
        return False


def show_error_popup(error_text):
    popup = Popup(title='App Error',
                  content=Label(text=error_text, font_size='16sp'),
                  size_hint=(0.9, 0.5))
    popup.open()

def global_exception_hook(exctype, value, tb):
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    print(error_message)
    from kivy.clock import Clock
    Clock.schedule_once(lambda dt: show_error_popup(error_message), 0)
    # Call the default excepthook too
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_hook


class NoteSpeakerApp(MDApp):
    def __init__(self):
        super().__init__()
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        
        # Initialize services
        self.config_service = ConfigService()
        self.speech_service = SpeechService(self.config_service)
        
        # Get API key from config or environment
        api_key = self.get_gemini_api_key()
        
        self.nlp_service = NLPService(api_key=api_key)
        
        # Initialize screens
        self.screen_manager = None
        self.main_screen = None
        self.settings_screen = None
        self.about_screen = None
        self.notes_screen = None
        
        # Set window size
        Window.size = (1200, 800)
        Window.minimum_width = 800
        Window.minimum_height = 600

    def get_gemini_api_key(self):
        """Get API key from config or environment and save to config if found in env."""
        api_key = self.config_service.get('gemini_api_key', None)
        if not api_key:
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                self.config_service.set('gemini_api_key', api_key)
                self.config_service.save_config()
        return api_key

    def build(self):
        # Register Hebrew fonts first and store result
        self.hebrew_font_available = register_hebrew_fonts()
        
        # Load saved language setting
        saved_language = self.config_service.get_language()
        self.speech_service.set_language(saved_language)
        
        print(f"Loaded saved language: {saved_language}")
        print(f"Config file location: {self.config_service.config_file}")
        
        # Ensure notes are loaded
        self.nlp_service.notes, self.nlp_service.last_note_id = self.nlp_service._load_notes_and_last_id()
        print(f"[DEBUG] Loaded {len(self.nlp_service.notes)} notes at startup")
        
        # Create the main layout
        self.main_layout = FloatLayout()
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Create screens
        self.main_screen = MainScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.notes_screen = NotesScreen(self)
        self.about_screen = HelpScreen(self)
        
        # Add screens to manager
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.settings_screen)
        self.screen_manager.add_widget(self.notes_screen)
        self.screen_manager.add_widget(self.about_screen)
        
        # Add screen manager to main layout
        self.main_layout.add_widget(self.screen_manager)
        
        # Overlay for menu (to detect taps outside menu) - ADD FIRST
        self.menu_overlay = Widget()
        self.menu_overlay.opacity = 0
        self.menu_overlay.bind(on_touch_down=self.on_overlay_touch)
        self.main_layout.add_widget(self.menu_overlay)
        
        # Create side menu (initially hidden) - ADD AFTER OVERLAY
        self.side_menu = SideMenu(self)
        self.side_menu.x = -self.side_menu.width  # Hide off-screen
        self.main_layout.add_widget(self.side_menu)
        
        # Start persistent logging to file
        LogService()
        
        return self.main_layout
    
    def show_side_menu(self, instance=None):
        """Show the side menu with animation"""
        # Animate menu sliding in
        anim = Animation(x=0, duration=0.3)
        anim.start(self.side_menu)
        
        # Show overlay
        overlay_anim = Animation(opacity=0.5, duration=0.3)
        overlay_anim.start(self.menu_overlay)
    
    def hide_side_menu(self, instance=None):
        """Hide the side menu with animation"""
        # Animate menu sliding out
        anim = Animation(x=-self.side_menu.width, duration=0.3)
        anim.start(self.side_menu)
        
        # Hide overlay
        overlay_anim = Animation(opacity=0, duration=0.3)
        overlay_anim.start(self.menu_overlay)
    
    def toggle_side_menu(self, instance=None):
        """Toggle the side menu visibility"""
        if self.side_menu.x >= -10:  # Menu is visible (account for animation tolerance)
            self.hide_side_menu()
        else:
            self.show_side_menu()
    
    def on_overlay_touch(self, instance, touch):
        """Handle touches on the overlay (outside menu)"""
        if self.menu_overlay.opacity > 0:  # Menu is open
            # Check if touch is within the side menu area
            if (touch.x >= self.side_menu.x and 
                touch.x <= self.side_menu.x + self.side_menu.width and
                touch.y >= self.side_menu.y and 
                touch.y <= self.side_menu.y + self.side_menu.height):
                # Touch is within side menu - don't handle it here
                print("DEBUG: Touch within side menu area - allowing side menu to handle")
                return False
            else:
                # Touch is outside side menu - close the menu
                print("DEBUG: Touch outside side menu - closing menu")
                self.hide_side_menu()
                return True
        return False
    
    def show_home_screen(self):
        """Navigate to home screen"""
        self.screen_manager.current = 'main'
    
    def show_settings_screen(self):
        """Navigate to settings screen"""
        print("DEBUG: show_settings_screen() called")
        print(f"DEBUG: Current screen: {self.screen_manager.current}")
        print(f"DEBUG: Available screens: {[screen.name for screen in self.screen_manager.screens]}")
        self.screen_manager.current = 'settings'
        print(f"DEBUG: Screen changed to: {self.screen_manager.current}")
    
    def show_notes_screen(self):
        """Navigate to notes screen"""
        print("DEBUG: show_notes_screen() called")
        self.screen_manager.current = 'notes'
    
    def show_help_screen(self):
        """Navigate to help screen"""
        print("DEBUG: show_help_screen() called")
        self.screen_manager.current = 'help'
    
    def listen(self, language=None, silence_timeout=5):
        """Delegate speech recognition to the service"""
        return self.speech_service.listen(language, silence_timeout)


# Run the app
if __name__ == '__main__':
    try:
        NoteSpeakerApp().run()
    except Exception as e:
        import traceback
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.label import Label
        from kivy.uix.popup import Popup
        from kivy.core.window import Window
        class ErrorApp(App):
            def build(self):
                layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
                error_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                label = Label(text=error_text, font_size='14sp', size_hint_y=0.9, text_size=(Window.width*0.8, None))
                btn = Button(text='OK', size_hint_y=0.1, height=40)
                layout.add_widget(label)
                layout.add_widget(btn)
                popup = Popup(title='Startup Error', content=layout, size_hint=(0.95, 0.95), auto_dismiss=False)
                btn.bind(on_release=lambda inst: App.get_running_app().stop())
                popup.open()
                return BoxLayout()  # Empty background
        ErrorApp().run() 