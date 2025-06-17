# -*- coding: utf-8 -*-
import kivy
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager
from kivy.animation import Animation
from kivy.core.text import LabelBase
import platform

# Import our custom modules
from app.widgets import SideMenu
from app.screens import MainScreen, SettingsScreen, NotesScreen, AboutScreen
from app.services import SpeechService, ConfigService

# Kivy requires minimum version
kivy.require('2.0.0')

# Register Hebrew-supporting fonts
def register_hebrew_fonts():
    """Register fonts that support Hebrew characters"""
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # Use macOS Hebrew-specific fonts
            font_paths = [
                "/System/Library/Fonts/SFHebrew.ttf",
                "/System/Library/Fonts/ArialHB.ttc",
                "/System/Library/Fonts/SFHebrewRounded.ttf",
                "/System/Library/Fonts/Arial.ttf", 
                "/System/Library/Fonts/Helvetica.ttc"
            ]
        elif system == "Windows":
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


class NoteSpeakerApp(App):
    def build(self):
        # Register Hebrew fonts first and store result
        self.hebrew_font_available = register_hebrew_fonts()
        
        # Initialize services
        self.config_service = ConfigService()
        self.speech_service = SpeechService()
        
        # Load saved language setting
        saved_language = self.config_service.get_language()
        self.speech_service.set_language(saved_language)
        
        print(f"Loaded saved language: {saved_language}")
        print(f"Config file location: {self.config_service.config_file}")
        
        # Create the main layout
        self.main_layout = FloatLayout()
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Create screens
        self.main_screen = MainScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.notes_screen = NotesScreen(self)
        self.about_screen = AboutScreen(self)
        
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
    
    def show_about_screen(self):
        """Navigate to about screen"""
        print("DEBUG: show_about_screen() called")
        self.screen_manager.current = 'about'
    
    def listen(self, language=None, silence_timeout=5):
        """Delegate speech recognition to the service"""
        return self.speech_service.listen(language, silence_timeout)


# Run the app
if __name__ == '__main__':
    NoteSpeakerApp().run() 