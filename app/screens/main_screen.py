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
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.uix.popup import Popup
import os
from bidi.algorithm import get_display
from app.widgets.note_graph_widget import NoteGraphWidget




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
        
        # --- Visualization section ---
        vis_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(220), padding=dp(10))
        vis_title = Label(text='Query and Visualization', font_size='18sp', color=(1,1,1,1), bold=True, size_hint_y=None, height=dp(30))
        self.graph_widget = NoteGraphWidget(fetch_note_by_id=self.fetch_note_by_id, get_language=self.get_language, fix_hebrew_display_direction=self.fix_hebrew_display_direction)
        vis_section.add_widget(vis_title)
        vis_section.add_widget(self.graph_widget)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(status_card)
        main_layout.add_widget(control_card)
        main_layout.add_widget(vis_section)
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
            text='Start',  # Changed from 'start'
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
        """Create notes display card with modern styling and a border around the chat scroll box"""
        chat_title = Label(
            text='Chat',
            font_size='20sp',
            color=(1, 1, 1, 1),
            bold=True,
            halign='left'
        )
        chat_title.text_size = (None, None)

        # Create a container for the scroll/chat with a border
        chat_container = BoxLayout(orientation='vertical', size_hint_y=1, padding=dp(8))
        with chat_container.canvas.before:
            from kivy.graphics import Color, RoundedRectangle, Line
            Color(0.2, 0.25, 0.35, 0.9)  # Card background
            chat_container.bg = RoundedRectangle(size=chat_container.size, pos=chat_container.pos, radius=[15])
            Color(0.5, 0.7, 1, 1)  # Border color (light blue)
            chat_container.border = Line(rounded_rectangle=[chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15], width=2)
            chat_container.bind(size=lambda instance, value: (setattr(chat_container.bg, 'size', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])),
                                 pos=lambda instance, value: (setattr(chat_container.bg, 'pos', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])))

        scroll = ScrollView()
        self.chat_history = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        scroll.add_widget(self.chat_history)

        # Keep the TextInput for compatibility and backup storage (hidden)
        self.notes_text = TextInput(
            text='',
            multiline=True,
            opacity=0,  # Hidden
            readonly=True
        )

        chat_container.add_widget(scroll)

        card = BoxLayout(orientation='vertical')
        card.add_widget(chat_title)
        card.add_widget(chat_container)
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
        self.record_btn.text = 'Start'  # Changed from 'start'
        self.record_btn.background_color = (0.2, 0.8, 0.3, 1)  # Green when ready
        self.stop_btn.disabled = True
        
        # Stop speech recognition
        self.app_instance.speech_service.stop_listening()
    
    def fix_hebrew_display_direction(self, text):
        """Fix Hebrew text direction for display in UI widgets"""
        if text is None:
            return ""  # Return empty string for None values
        current_lang = self.app_instance.config_service.get_language()
        if current_lang != 'he-IL':
            return str(text)
        result = get_display(str(text))
        return result

    def show_yes_no_dialog(self, note_text, result):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        label = Label(text="I didn't understand. Would you like to create a note with this text?")
        btn_layout = BoxLayout(orientation='horizontal', spacing=10)
        btn_yes = Button(text="Yes")
        btn_no = Button(text="No")
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        layout.add_widget(label)
        layout.add_widget(btn_layout)
        popup = Popup(title="Create Note?", content=layout, size_hint=(0.8, 0.4))

        def on_yes(instance):
            self.add_note_from_text(note_text)
            popup.dismiss()

        def on_no(instance):
            popup.dismiss()

        btn_yes.bind(on_press=on_yes)
        btn_no.bind(on_press=on_no)
        popup.open()

    def add_note_from_text(self, text):
        timestamp = self.format_timestamp()
        note_entry = f"[{timestamp}] {text}\n\n"
        current_notes = self.notes_text.text if self.notes_text.text else ""
        new_notes = current_notes + note_entry
        self.notes_text.text = new_notes
        current_lang = self.app_instance.config_service.get_language()
        if current_lang == 'he-IL':
            display_text = self.fix_hebrew_display_direction(new_notes)
            self.chat_history.text = display_text
        else:
            self.chat_history.text = new_notes
        preview = text[:30] + "..." if len(text) > 30 else text
        self.status_label.text = f'Added: "{preview}"'

    def translate_agent_message(self, message, lang):
        translations = {
            "Do you want me to create a note called": "האם ליצור רשומה בשם",
            "A note with the name": "רשומה בשם",
            "already exists. Do you want to override it?": "כבר קיימת. האם להחליף אותה?",
            "Created note:": "נוצרה רשומה:",
            "Note": "רשומה",
            "was overridden.": "הוחלפה.",
            "I couldn't understand your request. Please provide a clear instruction for your notes.": "לא הצלחתי להבין את הבקשה שלך. אנא נסח הוראה ברורה עבור הרשומות שלך.",
            "OK. I will create a note with the title": "בסדר. אצור רשומה עם הכותרת",
            "Note not found": "הרשומה לא נמצאה",
            "Creating a note with the title": "יוצר רשומה עם הכותרת",
            "Searching for notes related to": "מחפש רשומות הקשורות ל",
            "Note was overridden.": "הרשומה הוחלפה.",
            "yes": "כן",
            "no": "לא",
            "Found 1 note": "נמצאה רשומה אחת",
            "Found ": "נמצאו ",
            " notes": " רשומות"
        }
        if lang == 'he-IL' or (lang and lang.startswith('he')):
            # Special handling for 'Found X notes'
            import re
            match = re.match(r"Found (\d+) notes", message)
            if match:
                count = match.group(1)
                message = f"נמצאו {count} רשומות"
            elif message.strip() == "Found 1 note":
                message = "נמצאה רשומה אחת"
            else:
                for en, he in translations.items():
                    if en in message:
                        message = message.replace(en, he)
        return message

    # Hebrew and English chat prefixes
    HEBREW_USER_PREFIX = ':שמתשמ'
    HEBREW_AGENT_PREFIX = ':ןכוס'
    EN_USER_PREFIX = 'user:'
    EN_AGENT_PREFIX = 'agent:'

    def add_chat_message(self, sender, message):
        # sender: 'user' or 'agent'
        print(f"[DEBUG] add_chat_message: sender={sender}, original_message={message}")
        current_lang = self.app_instance.config_service.get_language()
        if sender == 'user':
            prefix = self.HEBREW_USER_PREFIX if current_lang.startswith('he') else self.EN_USER_PREFIX
        else:
            prefix = self.HEBREW_AGENT_PREFIX if current_lang.startswith('he') else self.EN_AGENT_PREFIX
        if current_lang == 'he-IL':
            fixed_message = self.fix_hebrew_display_direction(message)
            print(f"[DEBUG] add_chat_message: after fix_hebrew_display_direction: {fixed_message}")
            display_text = fixed_message + ' ' + prefix
            align = 'right'
        else:
            fixed_message = message
            display_text = prefix + ' ' + fixed_message
            align = 'left'
        color = (1, 1, 1, 1)
        font_name = 'app/fonts/Alef-Regular.ttf'
        if not os.path.exists(font_name):
            print("[WARNING] Alef Regular font not found. Text may not display correctly.")
        print(f"[DEBUG] Displaying message: {fixed_message} with font: {font_name}")
        label_kwargs = {
            "text": display_text,
            "size_hint_y": None,
            "height": 40,
            "color": color,  # White text for high contrast
            "halign": align,
            "valign": 'middle',
            "text_size": (self.chat_history.width - 40, None),
            "padding": (10, 5),
            "font_size": '20sp',
            "font_name": font_name
        }
        msg_label = Label(**label_kwargs)
        msg_label.canvas.before.clear()
        with msg_label.canvas.before:
            Color(0.7, 0.7, 0.7, 0.5)
            Line(rectangle=(msg_label.x, msg_label.y, msg_label.width, msg_label.height), width=1.2)
        self.chat_history.add_widget(msg_label)
        # Scroll to the bottom
        self.chat_history.parent.scroll_y = 0

    def on_speech_result(self, text):
        """Handle speech recognition result with modern feedback"""
        if text and text.strip():
            try:
                # Convert to proper Unicode if needed
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
                clean_text = text.strip()
                current_lang = self.app_instance.config_service.get_language()
                # Add user's message to chat
                self.add_chat_message('user', clean_text)
                # Use NLPService for natural language command processing
                result = self.app_instance.nlp_service.process_command(clean_text, current_lang)
                agent_msg = result.get("response", "")
                # Always translate agent message if app is set to Hebrew
                if current_lang == 'he-IL' or current_lang.startswith('he'):
                    agent_msg = self.translate_agent_message(agent_msg, current_lang)
                self.add_chat_message('agent', agent_msg)
                self.status_label.text = agent_msg
                # If needed, handle confirmation and listening logic as before
                if result["operation"] == "confirm":
                    self.app_instance.speech_service.start_listening(
                        on_result=self.on_speech_result,
                        on_error=self.on_speech_error,
                        on_auto_stop=self.on_auto_stop
                    )
                elif result["operation"] == "find" and "matches" in result:
                    notes = result["matches"]
                    relations = []
                    for note in notes:
                        if "relations" in note:
                            for rel_id in note["relations"]:
                                relations.append((note["id"], rel_id))
                    self.graph_widget.set_data(notes, relations)
                elif result["operation"] != "error":
                    self.refresh_notes_display()
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
        if hasattr(self, 'chat_history'):
            self.chat_history.clear_widgets()  # Remove all chat messages from the chat UI
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
            self.chat_history.text = f"[TEST] {test_text}\n\n"
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
        # Force refresh of app title in case language display name changed
        if hasattr(self.app_instance, 'root_window') and self.app_instance.root_window is not None:
            self.app_instance.root_window.title = self.get_app_title()
        # Update notes font and alignment based on current language
        self.update_notes_font()
        # Refresh the display with current language formatting
        self.refresh_notes_display()
    
    def refresh_notes_display(self):
        """Refresh the notes display based on current language"""
        if hasattr(self, 'notes_text') and hasattr(self, 'chat_history'):
            current_text = self.notes_text.text
            current_lang = self.app_instance.config_service.get_language()
            
            if current_lang == 'he-IL' and current_text:
                # Apply Hebrew direction fix
                display_text = self.fix_hebrew_display_direction(current_text)
                self.chat_history.text = display_text
            else:
                # Use text as-is for non-Hebrew languages
                self.chat_history.text = current_text
    
    def get_language_font(self):
        """Get the appropriate font for the current language"""
        import os
        font_path = 'app/fonts/Alef-Regular.ttf'
        if os.path.exists(font_path):
            print(f"Using Alef Regular font: {font_path}")
            return font_path
        print("[WARNING] Alef Regular font not found, using system default.")
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
        if hasattr(self, 'chat_history'):
            font_name = self.get_language_font()
            if font_name:  # Only set font_name if it's not None
                self.chat_history.font_name = font_name
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

    def fix_hebrew_quotes(self, text, lang):
        if lang.startswith("he"):
            # Replace standard double quotes with Hebrew gershayim
            text = text.replace('"', '״')
        return text 

    def fetch_note_by_id(self, note_id):
        # Helper to fetch a note by id from NLPService notes
        for note in self.app_instance.nlp_service.notes:
            if note.get('id') == note_id:
                return note
        return None 

    def get_language(self):
        return self.app_instance.config_service.get_language() 