from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock
import platform
import unicodedata
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle




class MainScreen(Screen):
    """Main screen for note taking"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'main'
        
        # Set modern gradient background
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            # Modern gradient background (dark blue to dark gray)
            Color(0.1, 0.15, 0.25, 1)  # Dark blue-gray
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_bg, pos=self._update_bg)
        
        self.setup_ui()
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def setup_ui(self):
        """Set up the main screen UI with modern styling"""
        main_layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(25))
        
        # Header with modern styling
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(80))
        
        # Menu button with modern styling
        menu_btn = Button(
            text='☰',
            size_hint=(None, 1),
            width=dp(60),
            font_size='24sp',
            background_color=(0.2, 0.6, 1.0, 1),  # Modern blue
            color=(1, 1, 1, 1),
            bold=True
        )
        menu_btn.bind(on_press=lambda x: self.app_instance.toggle_side_menu())
        
        # App title with modern typography
        title_label = Label(
            text=self.get_app_title(),
            font_size='26sp',
            bold=True,
            color=(1, 1, 1, 1),  # White text
            # Remove font_name to use default system font which supports Hebrew
        )
        
        header_layout.add_widget(menu_btn)
        header_layout.add_widget(title_label)
        
        # Status display with card styling
        status_card = self.create_status_card()
        
        # Control buttons with modern styling
        control_card = self.create_control_card()
        
        # Notes display with modern styling
        notes_card = self.create_notes_card()
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(status_card)
        main_layout.add_widget(control_card)
        main_layout.add_widget(notes_card)
        
        self.add_widget(main_layout)
        
        # Test Hebrew display - comment out for now
        # self.test_hebrew_display()
    
    def create_status_card(self):
        """Create status display card with modern styling"""
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=dp(20),
            spacing=dp(10)
        )
        
        # Add card background
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.25, 0.35, 0.9)  # Semi-transparent dark card
            card.bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[15])
            card.bind(size=lambda instance, value: setattr(card.bg, 'size', value))
            card.bind(pos=lambda instance, value: setattr(card.bg, 'pos', value))
        
        self.status_label = Label(
            text='Ready to record',  # Remove emoji
            font_size='18sp',
            color=(0.8, 0.9, 1.0, 1),  # Light blue
            bold=True
        )
        
        card.add_widget(self.status_label)
        return card
    
    def create_control_card(self):
        """Create control buttons card with modern styling"""
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=dp(20),
            spacing=dp(15)
        )
        
        # Add card background
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.25, 0.35, 0.9)  # Semi-transparent dark card
            card.bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[15])
            card.bind(size=lambda instance, value: setattr(card.bg, 'size', value))
            card.bind(pos=lambda instance, value: setattr(card.bg, 'pos', value))
        
        # Control buttons layout
        buttons_layout = BoxLayout(orientation='horizontal', spacing=dp(15))
        
        # Record button with modern styling
        self.record_btn = Button(
            text='Start Recording',  # Remove emoji
            font_size='16sp',
            background_color=(0.2, 0.8, 0.3, 1),  # Modern green
            color=(1, 1, 1, 1),
            bold=True
        )
        self.record_btn.bind(on_press=self.toggle_recording)
        
        # Stop button with modern styling
        self.stop_btn = Button(
            text='Stop',  # Remove emoji
            font_size='16sp',
            background_color=(0.9, 0.3, 0.3, 1),  # Modern red
            color=(1, 1, 1, 1),
            disabled=True,
            bold=True
        )
        self.stop_btn.bind(on_press=self.stop_recording)
        
        # Clear button with modern styling
        clear_btn = Button(
            text='Clear',  # Remove emoji
            font_size='16sp',
            background_color=(0.6, 0.4, 0.8, 1),  # Modern purple
            color=(1, 1, 1, 1),
            bold=True
        )
        clear_btn.bind(on_press=self.clear_notes)
        
        buttons_layout.add_widget(self.record_btn)
        buttons_layout.add_widget(self.stop_btn)
        buttons_layout.add_widget(clear_btn)
        
        card.add_widget(buttons_layout)
        return card
    
    def create_notes_card(self):
        """Create notes display card with modern styling"""
        card = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(10)
        )
        
        # Add card background
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.2, 0.25, 0.35, 0.9)  # Semi-transparent dark card
            card.bg = RoundedRectangle(size=card.size, pos=card.pos, radius=[15])
            card.bind(size=lambda instance, value: setattr(card.bg, 'size', value))
            card.bind(pos=lambda instance, value: setattr(card.bg, 'pos', value))
        
        # Notes title
        notes_title = Label(
            text='Your Notes',
            size_hint_y=None,
            height=dp(40),
            font_size='20sp',
            color=(1, 1, 1, 1),
            bold=True,
            halign='left'
        )
        notes_title.text_size = (None, None)
        
        # Scrollable notes area with simple Label
        scroll = ScrollView()
        
        # Use TextInput widget which handles Unicode better
        self.notes_display = TextInput(
            text='',
            font_size='16sp',
            foreground_color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 0),  # Transparent background
            multiline=True,
            readonly=True,
            cursor_color=(0, 0, 0, 0)  # Hide cursor
        )
        
        scroll.add_widget(self.notes_display)
        
        # Keep the TextInput for compatibility and backup storage
        self.notes_text = TextInput(
            text='',
            multiline=True,
            opacity=0,  # Hidden
            readonly=True
        )
        
        # For compatibility
        self.notes_label = self.notes_display
        
        card.add_widget(notes_title)
        card.add_widget(scroll)
        return card
    
    def get_app_title(self):
        """Get the app title with current language"""
        current_lang = self.app_instance.config_service.get_language()
        if current_lang in self.app_instance.speech_service.LANGUAGES:
            lang_name = self.app_instance.speech_service.LANGUAGES[current_lang]
            return f"🎙️ Note Speaker ({lang_name})"
        return "🎙️ Note Speaker"
    
    def toggle_recording(self, instance):
        """Toggle recording state with modern UI feedback"""
        if not self.app_instance.speech_service.is_listening:
            # Start recording
            self.start_recording()
        else:
            # Stop recording
            self.stop_recording(instance)
    
    def start_recording(self):
        """Start recording with modern UI updates"""
        self.status_label.text = 'Listening...'  # Remove emoji
        self.record_btn.text = 'Recording...'  # Remove emoji
        self.record_btn.background_color = (0.9, 0.3, 0.3, 1)  # Red when recording
        self.stop_btn.disabled = False
        
        # Get timeout settings from config
        silence_timeout = self.app_instance.config_service.get_silence_timeout()
        recording_timeout = self.app_instance.config_service.get_recording_timeout()
        
        # Start speech recognition with auto-stop features
        self.app_instance.speech_service.start_listening(
            on_result=self.on_speech_result,
            on_error=self.on_speech_error,
            on_auto_stop=self.on_auto_stop,
            silence_timeout=silence_timeout,
            recording_timeout=recording_timeout
        )
    
    def stop_recording(self, instance):
        """Stop recording with modern UI updates"""
        self.status_label.text = 'Ready to record'  # Remove emoji
        self.record_btn.text = 'Start Recording'  # Remove emoji
        self.record_btn.background_color = (0.2, 0.8, 0.3, 1)  # Green when ready
        self.stop_btn.disabled = True
        
        # Stop speech recognition
        self.app_instance.speech_service.stop_listening()
    
    def fix_hebrew_display_direction(self, text):
        """Fix Hebrew text direction for display in UI widgets"""
        current_lang = self.app_instance.config_service.get_language()
        
        if current_lang != 'he-IL':
            return text  # No changes for non-Hebrew
            
        # Check if text contains Hebrew characters
        has_hebrew = any('\u0590' <= char <= '\u05FF' for char in text)
        
        if not has_hebrew:
            return text  # No Hebrew characters found
        
        # Split into lines and process each line
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            if not line.strip():
                fixed_lines.append(line)  # Keep empty lines as-is
                continue
                
            # Check if line starts with timestamp [HH:MM]
            if line.startswith('[') and ']:' in line:
                # Split timestamp and content
                parts = line.split('] ', 1)
                if len(parts) == 2:
                    timestamp = parts[0] + '] '
                    content = parts[1]
                    
                    # Reverse only the Hebrew content part
                    if any('\u0590' <= char <= '\u05FF' for char in content):
                        # Reverse word order and characters within each word for Hebrew text
                        words = content.split()
                        reversed_words = []
                        for word in reversed(words):
                            # Check if word contains Hebrew characters
                            if any('\u0590' <= char <= '\u05FF' for char in word):
                                # Reverse characters within Hebrew words
                                reversed_words.append(word[::-1])
                            else:
                                # Keep non-Hebrew words as-is (numbers, punctuation, etc.)
                                reversed_words.append(word)
                        reversed_content = ' '.join(reversed_words)
                        fixed_line = timestamp + reversed_content
                    else:
                        fixed_line = line  # Keep non-Hebrew content as-is
                else:
                    fixed_line = line
            else:
                # Line without timestamp - reverse if Hebrew
                if any('\u0590' <= char <= '\u05FF' for char in line):
                    words = line.split()
                    reversed_words = []
                    for word in reversed(words):
                        # Check if word contains Hebrew characters
                        if any('\u0590' <= char <= '\u05FF' for char in word):
                            # Reverse characters within Hebrew words
                            reversed_words.append(word[::-1])
                        else:
                            # Keep non-Hebrew words as-is (numbers, punctuation, etc.)
                            reversed_words.append(word)
                    fixed_line = ' '.join(reversed_words)
                else:
                    fixed_line = line
                    
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)

    def on_speech_result(self, text):
        """Handle speech recognition result with modern feedback"""
        if text and text.strip():
            # Ensure proper Unicode handling for Hebrew text
            try:
                # Convert to proper Unicode if needed
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
                
                # Clean and validate the text
                clean_text = text.strip()
                
                # Simple timestamp
                timestamp = self.format_timestamp()
                
                # Use the text as-is since Google Speech API already provides correct direction
                processed_text = clean_text
                
                # Create the note entry manually
                note_entry = f"[{timestamp}] {processed_text}\n\n"
                
                # Update both the hidden TextInput and custom display
                current_notes = self.notes_text.text if self.notes_text.text else ""
                new_notes = current_notes + note_entry
                
                # Store original text in hidden TextInput
                self.notes_text.text = new_notes
                
                # Fix Hebrew direction only for display widget if language is Hebrew
                current_lang = self.app_instance.config_service.get_language()
                if current_lang == 'he-IL':
                    display_text = self.fix_hebrew_display_direction(new_notes)
                    self.notes_display.text = display_text
                else:
                    # For non-Hebrew languages, use text as-is
                    self.notes_display.text = new_notes
                
                # Create truncated preview for status
                preview = processed_text[:30] + "..." if len(processed_text) > 30 else processed_text
                self.status_label.text = f'Added: "{preview}"'
                
                print(f"Speech text (as received): {clean_text}")
                print(f"Using text as-is: {processed_text}")
                print(f"Timestamp: {timestamp}")
                
            except Exception as e:
                print(f"Error processing speech result: {e}")
                self.status_label.text = f'Error processing text: {e}'
        
        # Reset to listening state
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Ready to record'), 2)
    
    def on_speech_error(self, error):
        """Handle speech recognition error with modern feedback"""
        self.status_label.text = f'Error: {error}'  # Remove emoji
        
        # Reset UI state
        self.stop_recording(None)
        
        # Clear error after delay
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Ready to record'), 3)
    
    def on_auto_stop(self, reason):
        """Handle automatic stop due to silence or recording timeout"""
        self.status_label.text = f'Auto-stopped: {reason}'
        
        # Reset UI state
        self.stop_recording(None)
        
        # Clear message after delay
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Ready to record'), 3)
    
    def clear_notes(self, instance):
        """Clear all notes with modern confirmation"""
        self.notes_text.text = ''
        self.notes_display.text = ''
        self.status_label.text = 'Notes cleared'
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', 'Ready to record'), 2)
    
    def test_hebrew_display(self):
        """Test Hebrew text display"""
        # Only add test text if Hebrew is configured
        current_lang = self.app_instance.config_service.get_language()
        
        if current_lang == 'he-IL':
            test_text = "שלום עולם - מערכת זיהוי דיבור"
            print(f"Testing Hebrew display: {test_text}")
        else:
            test_text = "Hello World - Speech Recognition System"
            print(f"Testing English display: {test_text}")
        
        # Add test text after a short delay to ensure UI is ready
        def add_test_text(dt):
            self.notes_display.text = f"[TEST] {test_text}\n\n"
            self.notes_text.text = f"[TEST] {test_text}\n\n"
        
        Clock.schedule_once(add_test_text, 1)
    
    def on_enter(self):
        """Called when entering the main screen"""
        # Update title to reflect current language
        if hasattr(self, 'children') and self.children:
            # Find and update the title label
            for child in self.children[0].children:
                if hasattr(child, 'children') and len(child.children) > 1:
                    title_widget = child.children[0]  # Title is the second widget (index 0 due to reverse order)
                    if hasattr(title_widget, 'text'):
                        title_widget.text = self.get_app_title()
                        break
        
        # Update notes font and alignment based on current language
        self.update_notes_font()
        # Refresh the display with current language formatting
        self.refresh_notes_display()
    
    def refresh_notes_display(self):
        """Refresh the notes display based on current language"""
        if hasattr(self, 'notes_text') and hasattr(self, 'notes_display'):
            current_text = self.notes_text.text
            current_lang = self.app_instance.config_service.get_language()
            
            if current_lang == 'he-IL' and current_text:
                # Apply Hebrew direction fix
                display_text = self.fix_hebrew_display_direction(current_text)
                self.notes_display.text = display_text
            else:
                # Use text as-is for non-Hebrew languages
                self.notes_display.text = current_text
    
    def get_language_font(self):
        """Get the appropriate font for the current language"""
        current_lang = self.app_instance.config_service.get_language()
        import os
        
        if current_lang == 'he-IL':
            # Try fonts that support both Hebrew and English
            hebrew_fonts = [
                '/System/Library/Fonts/Arial.ttf',  # Best choice - supports both Hebrew and English
                '/System/Library/Fonts/Arial Hebrew.ttc',
                '/System/Library/Fonts/ArialHB.ttc', 
                '/System/Library/Fonts/SFHebrew.ttf'
            ]
            
            for font_path in hebrew_fonts:
                if os.path.exists(font_path):
                    print(f"Using font for Hebrew: {font_path}")
                    return font_path
            
            print("No Hebrew font found, using default")
            return None
        else:
            # For English and other languages, use system default or Arial
            english_fonts = [
                '/System/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc'
            ]
            
            for font_path in english_fonts:
                if os.path.exists(font_path):
                    print(f"Using font for English: {font_path}")
                    return font_path
            
            print("Using system default font for English")
            return None
    
    def get_text_alignment(self):
        """Get the appropriate text alignment for the current language"""
        current_lang = self.app_instance.config_service.get_language()
        
        if current_lang == 'he-IL':
            return 'left'  # Use left alignment for consistent display
        else:
            return 'left'  # English is LTR
    
    def update_notes_font(self):
        """Update the notes display font based on current language"""
        if hasattr(self, 'notes_display'):
            font_name = self.get_language_font()
            if font_name:  # Only set font_name if it's not None
                self.notes_display.font_name = font_name
            # TextInput doesn't have halign, so skip that
    
    def format_timestamp(self):
        """Create a simple timestamp using only basic ASCII numbers and colon"""
        from datetime import datetime
        now = datetime.now()
        
        # Get hour and minute
        hour = now.hour
        minute = now.minute
        
        # Convert to individual digits
        hour_tens = hour // 10
        hour_ones = hour % 10
        minute_tens = minute // 10
        minute_ones = minute % 10
        
        # Build timestamp character by character using basic ASCII
        timestamp = str(hour_tens) + str(hour_ones) + str(minute_tens) + str(minute_ones)
        
        # Insert colon manually
        result = timestamp[0] + timestamp[1] + ":" + timestamp[2] + timestamp[3]
        
        return result 