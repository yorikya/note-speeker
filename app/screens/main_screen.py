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
        self.current_note_context = None  # Track selected note
        self.status_label = None  # Will hold the status label
        
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
        self.title_label = Label(
            text=self.get_app_title(),
            font_size='26sp',
            bold=True,
            color=(1, 1, 1, 1),  # White text
            # Remove font_name to use default system font which supports Hebrew
        )
        
        header_layout.add_widget(menu_btn)
        header_layout.add_widget(self.title_label)
        
        # Status display with card styling
        status_card = self.create_status_card()
        
        # Control buttons with modern styling
        control_card = self.create_control_card()
        
        # Notes display with modern styling
        notes_card = self.create_notes_card()
        
        # --- Visualization section ---
        vis_section = BoxLayout(orientation='vertical', size_hint_y=0.6, padding=dp(10), spacing=dp(10))
        with vis_section.canvas.before:
            Color(0.15, 0.2, 0.3, 0.9)  # Darker card background
            self.vis_bg = RoundedRectangle(size=vis_section.size, pos=vis_section.pos, radius=[15])
            vis_section.bind(size=lambda instance, value: setattr(self.vis_bg, 'size', value))
            vis_section.bind(pos=lambda instance, value: setattr(self.vis_bg, 'pos', value))

        vis_section.add_widget(Label(
            text="Query and Visualization",
            size_hint_y=None,
            height=dp(40),
            font_size='20sp'
        ))
        
        # Create graph widget
        self.graph_widget = NoteGraphWidget(size_hint=(1, 1))
        vis_section.add_widget(self.graph_widget)
        
        main_layout.add_widget(header_layout)
        main_layout.add_widget(status_card)
        main_layout.add_widget(control_card)
        main_layout.add_widget(vis_section)
        main_layout.add_widget(notes_card)
        
        # Add status line at the bottom
        self.status_label = Label(
            text="Ready to record",
            size_hint=(1, None),
            height=dp(30),
            halign='right',
            valign='middle',
            font_name='app/fonts/Alef-Regular.ttf'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        main_layout.add_widget(self.status_label)
        
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

        # Card layout for notes
        card = BoxLayout(
            orientation='vertical',
            size_hint_y=0.4,
            padding=dp(10),
            spacing=dp(10)
        )
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
        print("[DEBUG] stop_recording: Stopping speech service.")
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
    # HEBREW_USER_PREFIX = ':שמתשמ'
    # HEBREW_AGENT_PREFIX = ':ןכוס'
    HEBREW_USER_PREFIX = 'משתמש:'
    HEBREW_AGENT_PREFIX = 'סוכן:'
    EN_USER_PREFIX = 'user:'
    EN_AGENT_PREFIX = 'agent:'

    def add_chat_message(self, sender, message):
        """Add a message to the chat history with modern styling"""
        # Determine prefix and alignment based on sender and language
        current_lang = self.app_instance.config_service.get_language()
        is_hebrew = current_lang == 'he-IL'

        if is_hebrew:
            prefix = self.HEBREW_AGENT_PREFIX if sender == 'agent' else self.HEBREW_USER_PREFIX
        else:
            prefix = self.EN_AGENT_PREFIX if sender == 'agent' else self.EN_USER_PREFIX

        # Translate message if needed
        original_message = message
        if is_hebrew and sender == 'agent':
            message = self.translate_agent_message(message, 'he-IL')


        full_message = f"{prefix} {message}"

        # Apply bidi algorithm for display
        display_message = self.fix_hebrew_display_direction(full_message)

        print(f"[DEBUG] add_chat_message: sender={sender}, original_message={original_message}")
        if is_hebrew:
            print(f"[DEBUG] add_chat_message: after fix_hebrew_display_direction: {display_message}")

        # Choose font based on language
        font_name = self.get_language_font()
        print(f"[DEBUG] Displaying message: {display_message} with font: {font_name}")

        # Create the chat message label
        message_label = Label(
            text=display_message,
            font_name=font_name,
            size_hint_y=None,
            font_size='16sp',
            padding=(dp(10), dp(10))
        )

        # Set text alignment and size properties
        message_label.bind(width=lambda s, w: s.setter('text_size')(s, (w, None)))

        # Add a background color to the message label for better readability
        with message_label.canvas.before:
            Color(0.25, 0.3, 0.4, 0.7 if sender == 'user' else 0.5)  # Different colors for user/agent
            message_label.bg_rect = RoundedRectangle(
                size=message_label.size, pos=message_label.pos, radius=[10]
            )
            message_label.bind(size=lambda instance, value: setattr(message_label.bg_rect, 'size', value))
            message_label.bind(pos=lambda instance, value: setattr(message_label.bg_rect, 'pos', value))

        # Create a container to handle the alignment of the message bubble
        align_container = BoxLayout(
            size_hint_y=None,
            height=message_label.height
        )
        
        # Align all messages based on language direction
        if is_hebrew:
            # Right-to-left alignment for Hebrew
            message_label.halign = 'right'
            align_container.add_widget(Widget())  # Spacer
            align_container.add_widget(message_label)
        else:
            # Left-to-right alignment for English
            message_label.halign = 'left'
            align_container.add_widget(message_label)
            align_container.add_widget(Widget())  # Spacer

        self.chat_history.add_widget(align_container)

        # Auto-scroll to the bottom
        self.chat_history.parent.scroll_y = 0

        # Speak agent messages
        if sender == 'agent':
            # Run TTS in a separate thread to avoid blocking the UI
            import threading
            threading.Thread(
                target=self.app_instance.speech_service.speak_text,
                args=(message,),
                daemon=True
            ).start()

    def on_speech_result(self, text):
        """Handle speech recognition result with modern feedback"""
        print(f"[DEBUG] on_speech_result: Recognized text: '{text}'")
        self.status_label.text = f'Recognized: "{text[:50]}..."'
        self.add_chat_message('user', text)  # Add user's speech to chat
        
        # Process the command through the NLP service
        self.process_command(text)
        
    def on_speech_error(self, error):
        """Handle speech recognition error"""
        self.status_label.text = f'Error: {error}'
        self.stop_recording(None)  # Stop on error

    def on_auto_stop(self, reason):
        """Handle auto-stop event from speech service"""
        self.status_label.text = f"Stopped: {reason}"
        self.stop_recording(None)

    def clear_notes(self, instance):
        """Clear all notes and chat history"""
        self.notes_text.text = ""
        self.chat_history.clear_widgets()
        self.status_label.text = 'Cleared all notes.'

    def test_hebrew_display(self):
        """Function to test Hebrew text rendering"""
        hebrew_text = "שלום עולם, זוהי בדיקה."
        english_text = "Hello world, this is a test."
        
        # Add Hebrew text
        self.add_chat_message('user', hebrew_text)
        self.add_chat_message('agent', hebrew_text)
        
        # Add English text
        self.add_chat_message('user', english_text)
        self.add_chat_message('agent', english_text)

        def add_test_text(dt):
            self.notes_text.text += f"{hebrew_text}\n{english_text}\n"
        Clock.schedule_once(add_test_text, 1)

    def on_enter(self):
        """Called when the screen is displayed"""
        # Load notes from NLPService
        self.app_instance.nlp_service._load_notes()
        
        # Refresh graph and notes display
        self.refresh_notes_display()
        
        # Update UI components based on language
        self.update_notes_font()
        
        # Update app title
        self.title_label.text = self.get_app_title()

    def refresh_notes_display(self):
        """Refresh notes display from NLPService"""
        notes = self.app_instance.nlp_service.notes
        relations = self.app_instance.nlp_service.get_relations()
        
        # Update graph widget
        self.graph_widget.set_data(notes, relations)
        
        # Update chat history (if needed, or just clear)
        # self.chat_history.clear_widgets() # Decide if you want to clear chat on refresh

    def get_language_font(self):
        """Get the appropriate font based on the current language"""
        current_lang = self.app_instance.config_service.get_language()
        if current_lang == 'he-IL':
            return 'app/fonts/Alef-Regular.ttf'
        # Default font for English and other languages
        return 'app/fonts/NotoSans-Regular.ttf'

    def get_text_alignment(self, sender):
        """Get text alignment based on language and sender"""
        current_lang = self.app_instance.config_service.get_language()
        if current_lang == 'he-IL':
            # For Hebrew (RTL), agent is on the right, user on the left
            return 'right' if sender == 'agent' else 'left'
        else:
            # For English (LTR), user is on the right, agent on the left
            return 'right' if sender == 'user' else 'left'

    def update_notes_font(self):
        """Update font for all relevant widgets"""
        font_name = self.get_language_font()
        self.status_label.font_name = font_name
        # Update chat labels if they exist
        for child in self.chat_history.children:
            if isinstance(child, Label):
                child.font_name = font_name

    def format_timestamp(self):
        """Format the current time as a timestamp"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def fix_hebrew_quotes(self, text, lang):
        """Fix quotes for Hebrew NLP processing"""
        if lang == 'he-IL':
            return text.replace('"', '')
        return text

    def fetch_note_by_id(self, note_id):
        # Helper to fetch a note by id from NLPService notes
        return self.app_instance.nlp_service.get_note_by_id(note_id)

    def get_language(self):
        return self.app_instance.config_service.get_language()

    def update_note_context(self, note):
        """Update the current note context."""
        self.current_note_context = note
        if note:
            self.status_label.text = f"Context: {note.get('title', 'N/A')}"
        else:
            self.status_label.text = "Context cleared"

    def process_command(self, command_text):
        """Process a command using the NLPService and update the UI."""
        
        # Fix quotes for hebrew
        fixed_command = self.fix_hebrew_quotes(
            command_text,
            self.get_language()
        )
        
        response = self.app_instance.nlp_service.process_command(
            fixed_command,
            language=self.get_language()
        )
        print(f"[DEBUG] NLP Response: {response}")
        
        # Add agent's response to chat
        if response.get("response"):
            self.add_chat_message('agent', response["response"])
        
        # Handle notes update
        if response.get("notes_updated"):
            # Fetch all notes to display
            all_notes = self.app_instance.nlp_service.notes
            relations = self.app_instance.nlp_service.get_relations()
            
            # If the command found specific notes, show only them and their connections
            found_notes_data = response.get("found_notes")
            if found_notes_data:
                
                # Create a set of IDs to display: found notes, their parents, and their children
                found_ids = {note['id'] for note in found_notes_data}
                display_ids = set(found_ids)
                
                for note_id in found_ids:
                    note = self.fetch_note_by_id(note_id)
                    if note:
                        if note.get('parent_id'):
                            display_ids.add(note['parent_id'])
                        if note.get('children'):
                            display_ids.update(note.get('children'))

                # Filter the notes and relations to only include the ones to be displayed
                notes_to_display = [note for note in all_notes if note['id'] in display_ids]
                self.graph_widget.set_data(notes_to_display, relations)
            else:
                # Otherwise, display the full graph
                self.graph_widget.set_data(all_notes, relations)

        # Stop listening unless confirmation is required
        if not response.get("requires_confirmation"):
            print("[DEBUG] Confirmation not required. Stopping recording.")
            self.stop_recording(None)
        else:
            print("[DEBUG] Confirmation required. Keeping microphone open.")

    def create_sub_note(self, title):
        """Create a sub-note under the current context."""
        if not self.current_note_context:
            self.add_chat_message('agent', "Please select a parent note first.")
            return

        parent_id = self.current_note_context['id']
        command = f"create a note titled '{title}' as a child of '{parent_id}'"
        self.process_command(command) 