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
        self.accumulating_description = False
        self.accumulated_speech = []
        self.pending_update_type = None
        self.pending_note_title = None
        self.welcome_shown = False  # Track if welcome message was already shown
        
        # Set modern gradient background
        with self.canvas.before:
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
        main_layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))

        # --- Header with side menu, title, and compact controls ---
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))

        # Menu button
        menu_btn = Button(
            text='☰',
            size_hint=(None, 1),
            width=dp(40),
            font_size='20sp',
            background_color=(0.2, 0.6, 1.0, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        menu_btn.bind(on_press=lambda x: self.app_instance.toggle_side_menu())

        # App title
        self.title_label = Label(
            text=self.get_app_title(),
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_x=0.5,
            halign='left',
            valign='middle'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))

        # Compact control buttons
        self.record_btn = Button(
            text='Start',
            size_hint=(None, 1),
            width=dp(90),
            height=dp(40),
            font_size='14sp',
            background_color=(0.2, 0.8, 0.3, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        self.record_btn.bind(on_press=self.toggle_recording)
        self.stop_btn = Button(
            text='Stop',
            size_hint=(None, 1),
            width=dp(90),
            height=dp(40),
            font_size='14sp',
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            disabled=True,
            bold=True
        )
        self.stop_btn.bind(on_press=self.stop_recording)
        clear_btn = Button(
            text='Clear',
            size_hint=(None, 1),
            width=dp(90),
            height=dp(40),
            font_size='14sp',
            background_color=(0.6, 0.4, 0.8, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        clear_btn.bind(on_press=self.clear_notes)

        header_layout.add_widget(menu_btn)
        header_layout.add_widget(self.title_label)
        header_layout.add_widget(self.record_btn)
        header_layout.add_widget(self.stop_btn)
        header_layout.add_widget(clear_btn)

        # --- Visualization section (top, 55%) ---
        vis_section = BoxLayout(orientation='vertical', size_hint_y=0.55, padding=dp(5), spacing=dp(5))
        with vis_section.canvas.before:
            Color(0.15, 0.2, 0.3, 0.9)
            self.vis_bg = RoundedRectangle(size=vis_section.size, pos=vis_section.pos, radius=[15])
            vis_section.bind(size=lambda instance, value: setattr(self.vis_bg, 'size', value))
            vis_section.bind(pos=lambda instance, value: setattr(self.vis_bg, 'pos', value))
        vis_section.add_widget(Label(
            text="Query and Visualization",
            size_hint_y=None,
            height=dp(30),
            font_size='16sp'
        ))
        graph_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=True)
        self.graph_widget = NoteGraphWidget(size_hint=(None, None), size=(1600, 1000))
        graph_scroll.add_widget(self.graph_widget)
        vis_section.add_widget(graph_scroll)

        # --- Chat section (bottom, 45%) ---
        chat_section = BoxLayout(orientation='vertical', size_hint_y=0.45, padding=dp(5), spacing=dp(5))
        chat_title = Label(
            text='Chat',
            font_size='16sp',
            color=(1, 1, 1, 1),
            bold=True,
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        chat_title.text_size = (None, None)
        chat_container = BoxLayout(orientation='vertical', size_hint_y=1, padding=dp(4))
        with chat_container.canvas.before:
            Color(0.2, 0.25, 0.35, 0.9)
            chat_container.bg = RoundedRectangle(size=chat_container.size, pos=chat_container.pos, radius=[15])
            Color(0.5, 0.7, 1, 1)
            chat_container.border = Line(rounded_rectangle=[chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15], width=2)
            chat_container.bind(size=lambda instance, value: (setattr(chat_container.bg, 'size', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])),
                                 pos=lambda instance, value: (setattr(chat_container.bg, 'pos', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])))
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        self.chat_history = BoxLayout(orientation='vertical', size_hint_y=None, spacing=0)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        scroll.add_widget(self.chat_history)
        self.notes_text = TextInput(
            text='',
            multiline=True,
            opacity=0,
            readonly=True
        )
        chat_container.add_widget(scroll)
        chat_section.add_widget(chat_title)
        chat_section.add_widget(chat_container)

        # --- Assemble main layout ---
        main_layout.add_widget(header_layout)
        main_layout.add_widget(vis_section)
        main_layout.add_widget(chat_section)

        # Only keep the status at the bottom
        status_layout = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(30), padding=[dp(10), 0, dp(10), 0], spacing=dp(10))
        self.status_label = Label(
            text="Ready to record",
            size_hint=(None, 1),
            width=dp(180),
            halign='right',
            valign='middle',
            font_name='app/fonts/Alef-Regular.ttf'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        # Add pipe and extra space between status and prefix
        self.status_pipe_label = Label(
            text="   |   ",
            size_hint=(None, 1),
            width=dp(40),
            halign='center',
            valign='middle',
            font_name='app/fonts/Alef-Regular.ttf'
        )
        self.status_pipe_label.bind(size=self.status_pipe_label.setter('text_size'))
        # Reduce space between prefix and bar
        self.energy_prefix_label = Label(
            text="Voice:",
            size_hint=(None, 1),
            width=dp(60),
            halign='right',
            valign='middle',
            font_name='app/fonts/Alef-Regular.ttf'
        )
        self.energy_prefix_label.bind(size=self.energy_prefix_label.setter('text_size'))
        self.energy_bar = Widget(size_hint=(0.035, 1))  # Halve the width
        with self.energy_bar.canvas:
            self.energy_bar_color = Color(0.2, 0.9, 0.3, 1)  # Green
            self.energy_bar_rect = Rectangle(pos=(self.energy_bar.x, self.energy_bar.y + (self.energy_bar.height - dp(18)) / 2), size=(0, dp(18)))
            self.energy_bar_border = Line(rectangle=(self.energy_bar.x, self.energy_bar.y + (self.energy_bar.height - dp(18)) / 2, self.energy_bar.width, dp(18)), width=1.2)
        def update_bar_pos(instance, value):
            bar_height = dp(18)
            bar_y = self.energy_bar.y + (self.energy_bar.height - bar_height) / 2
            self.energy_bar_rect.pos = (self.energy_bar.x, bar_y)
            self.energy_bar_rect.size = (self.energy_bar_rect.size[0], bar_height)
            self.energy_bar_border.rectangle = (self.energy_bar.x, bar_y, self.energy_bar.width, bar_height)
        self.energy_bar.bind(pos=update_bar_pos, size=update_bar_pos)
        status_layout.add_widget(self.status_label)
        status_layout.add_widget(self.status_pipe_label)
        status_layout.add_widget(self.energy_prefix_label)
        status_layout.add_widget(self.energy_bar)
        main_layout.add_widget(status_layout)
        # Schedule energy bar update
        def update_energy_bar(dt):
            energy = self.app_instance.speech_service.get_energy_level()
            # Bar width: max 1000, fill parent width
            bar_max_width = self.energy_bar.width
            bar_height = dp(18)
            bar_width = min(max(energy / 1000.0, 0.0), 1.0) * bar_max_width
            bar_y = self.energy_bar.y + (self.energy_bar.height - bar_height) / 2
            self.energy_bar_rect.pos = (self.energy_bar.x, bar_y)
            self.energy_bar_rect.size = (bar_width, bar_height)
            self.energy_bar_border.rectangle = (self.energy_bar.x, bar_y, self.energy_bar.width, bar_height)
        Clock.schedule_interval(update_energy_bar, 1)

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
            Color(0.2, 0.25, 0.35, 0.9)  # Card background
            chat_container.bg = RoundedRectangle(size=chat_container.size, pos=chat_container.pos, radius=[15])
            Color(0.5, 0.7, 1, 1)  # Border color (light blue)
            chat_container.border = Line(rounded_rectangle=[chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15], width=2)
            chat_container.bind(size=lambda instance, value: (setattr(chat_container.bg, 'size', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])),
                                 pos=lambda instance, value: (setattr(chat_container.bg, 'pos', value), setattr(chat_container.border, 'points', [chat_container.x, chat_container.y, chat_container.x+chat_container.width, chat_container.y, chat_container.x+chat_container.width, chat_container.y+chat_container.height, chat_container.x, chat_container.y+chat_container.height, chat_container.x, chat_container.y]), setattr(chat_container.border, 'rounded_rectangle', [chat_container.x, chat_container.y, chat_container.width, chat_container.height, 15])))

        # Replace ScrollView with DebugScrollView for debugging
        scroll = ScrollView()
        self.chat_history = BoxLayout(orientation='vertical', size_hint_y=None, spacing=0)
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
            size_hint_y=None,
            height=dp(500),  # Increased height for 7+ lines
            padding=dp(5),   # Reduced padding
            spacing=dp(5)    # Reduced spacing
        )
        card.add_widget(chat_title)
        card.add_widget(chat_container)
        return card

    def get_app_title(self):
        """Get the app title with current language"""
        current_lang = self.app_instance.config_service.get_language()
        if current_lang in self.app_instance.speech_service.LANGUAGES:
            lang_name = self.app_instance.speech_service.LANGUAGES[current_lang]
            return f"Note Speaker ({lang_name})"
        return "Note Speaker"
    
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
        self.status_label.text = 'Listening...'
        self.record_btn.text = 'Recording...'
        self.record_btn.background_color = (0.9, 0.3, 0.3, 1)
        self.stop_btn.disabled = False
        # Get timeout settings from config
        silence_timeout = self.app_instance.config_service.get_silence_timeout()
        recording_timeout = self.app_instance.config_service.get_recording_timeout()
        print(f"[DEBUG] start_recording: silence_timeout={silence_timeout}, recording_timeout={recording_timeout}")
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
        print("[DEBUG] stop_recording: Stopping speech service.")
        self.app_instance.speech_service.stop_listening()
        if self.accumulating_description:
            full_text = ' '.join(self.accumulated_speech)
            self.accumulating_description = False
            self.accumulated_speech = []
            if self.pending_update_type and self.pending_note_title:
                self.update_note_description_direct(self.pending_note_title, full_text, self.pending_update_type)
            self.pending_update_type = None
            self.pending_note_title = None
    
    def update_note_description_direct(self, note_title, new_text, update_type):
        # Directly update the note description or append, bypassing process_command chat flow
        nlp_service = self.app_instance.nlp_service
        # Find the note by title
        note = next((n for n in nlp_service.notes if n.get('title') == note_title), None)
        if not note:
            self.add_chat_message('agent', f"Note '{note_title}' not found.")
            return
        if update_type == 'replace_description':
            note['description'] = new_text
        elif update_type == 'append_description':
            current_desc = note.get('description', '')
            if current_desc:
                note['description'] = current_desc + '\n' + new_text
            else:
                note['description'] = new_text
        nlp_service._save_notes()
        lang = self.get_language()
        if lang == 'he-IL':
            msg = f"התיאור עודכן לרשומה '{note_title}'"
        else:
            msg = f"The description for '{note_title}' was updated."
        self.add_chat_message('agent', msg)
        self.refresh_notes_display()
    
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
            " notes": " רשומות",
            # New for update/delete/sub-note flow:
            "Found 1 note. Would you like to update, delete, or add a sub-note?": "נמצאה רשומה אחת. האם תרצה לעדכן, למחוק או להוסיף תת-רשומה?",
            "Would you like to update, delete, or add a sub-note?": "האם תרצה לעדכן, למחוק או להוסיף תת-רשומה?",
            "Add a sub-note called": "להוסיף תת-רשומה בשם",
            "under": "תחת",
            "Please specify if you want to update, delete, or add a sub-note, or confirm/cancel.": "אנא ציין אם ברצונך לעדכן, למחוק או להוסיף תת-רשומה, או אשר/בטל.",
            "Content updated": "התוכן עודכן",
            "OK, I've cancelled the action.": "בסדר, ביטלתי את הפעולה.",
            "Deleted note:": "הרשומה נמחקה:",
            "Updating content of": "מעדכן את התוכן של",
            "was updated.": "עודכן.",
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

    def add_chat_message(self, sender, message, requires_confirmation=False, suppress_tts=False):
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

        # Set background color based on sender
        if sender == 'user':
            bubble_color = (0.22, 0.32, 0.45, 0.92)  # Muted blue for user
        else:
            bubble_color = (0.28, 0.45, 0.32, 0.92)  # Muted green for agent

        # Create the chat message label with reduced padding
        message_label = Label(
            text=display_message,
            font_name=font_name,
            size_hint_y=None,
            font_size='16sp',
            padding=(dp(2), dp(2))  # Further reduced padding for compactness
        )

        # Set text alignment and size properties
        message_label.bind(width=lambda s, w: s.setter('text_size')(s, (w, None)))

        # Add a background color to the message label for better readability
        with message_label.canvas.before:
            Color(*bubble_color)
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
        if sender == 'agent' and not suppress_tts:
            from app.services.nlp_service import WELCOME_MESSAGE_EN, WELCOME_MESSAGE_HE
            if message.strip() in (WELCOME_MESSAGE_EN.strip(), WELCOME_MESSAGE_HE.strip()):
                return
            print("[DEBUG] Stopping microphone before TTS playback.")
            self.app_instance.speech_service.stop_listening()
            def tts_and_resume():
                self.app_instance.speech_service.speak_text(message)
                if requires_confirmation:
                    import time
                    time.sleep(0.5)
                    print("[DEBUG] Resuming microphone after TTS playback (confirmation required, with delay).")
                    self.start_recording()
            import threading
            threading.Thread(target=tts_and_resume, daemon=True).start()

    def on_speech_result(self, text):
        """Handle speech recognition result with modern feedback"""
        print(f"[DEBUG] on_speech_result: Recognized text: '{text}'")
        self.status_label.text = f'Recognized: "{text[:50]}..."'
        self.add_chat_message('user', text)
        if self.accumulating_description:
            self.accumulated_speech.append(text)
        else:
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
        self.chat_history.clear_widgets()  # Clear chat on app load
        if not self.welcome_shown:
            show_welcome = self.app_instance.config_service.get('show_welcome_message', True)
            if show_welcome:
                lang = self.get_language()
                from app.services.nlp_service import WELCOME_MESSAGE_EN, WELCOME_MESSAGE_HE
                msg = WELCOME_MESSAGE_HE if lang == 'he-IL' else WELCOME_MESSAGE_EN
                self.show_welcome_popup(msg)
            self.welcome_shown = True
        # Load notes from NLPService
        self.app_instance.nlp_service.notes, self.app_instance.nlp_service.last_note_id = self.app_instance.nlp_service._load_notes_and_last_id()
        
        # Refresh graph and notes display
        self.refresh_notes_display()
        
        # Clear visualization on load
        self.clear_visualization()
        
        # Update UI components based on language
        self.update_notes_font()
        
        # Update app title
        self.title_label.text = self.get_app_title()

    def refresh_notes_display(self):
        """Refresh notes display from NLPService"""
        notes = self.app_instance.nlp_service.notes
        relations = self.app_instance.nlp_service.get_relations()
        print("[DEBUG] refresh_notes_display: Visualizing notes:")
        for note in notes:
            print(f"  ID: {note.get('id')}, Title: {note.get('title')}")
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
        lang = self.get_language()
        is_hebrew = lang == 'he-IL'
        # Detect update/append description intent
        # (Old trigger code removed; all commands now handled by NLPService/tool selection)
        lower_cmd = command_text.lower()
        # Check for note context (from find or selection)
        note_title = None
        if self.current_note_context:
            note_title = self.current_note_context.get('title')
        # If last find returned one note, use it
        # (You may want to store last found note in a variable for robustness)
        # Detect triggers
        # Default: send to NLPService
        response = self.app_instance.nlp_service.process_command(
            fixed_command,
            language=lang
        )
        print(f"[DEBUG] NLP Response: {response}")
        
        # Add agent's response to chat
        if response.get("response"):
            self.add_chat_message('agent', response["response"], requires_confirmation=response.get("requires_confirmation", False))
        
        # Only update visualization if a search was performed and found_notes is present
        found_notes_data = response.get("found_notes") or response.get("matches")
        if found_notes_data:
            all_notes = self.app_instance.nlp_service.notes
            relations = self.app_instance.nlp_service.get_relations()
            all_notes_by_id = {note['id']: note for note in all_notes}

            found_ids = {note['id'] for note in found_notes_data}
            display_ids = set(found_ids)

            # Add parents and children (only direct)
            for note_id in list(found_ids):
                note = all_notes_by_id.get(note_id)
                if note:
                    parent_id = note.get('parent_id')
                    if parent_id and parent_id in all_notes_by_id:
                        display_ids.add(parent_id)
                    children = note.get('children', [])
                    for child_id in children:
                        if child_id in all_notes_by_id:
                            display_ids.add(child_id)

            # Only show notes that are in display_ids
            notes_to_display = [note for note in all_notes if note['id'] in display_ids]
            # Only show relations between displayed notes
            filtered_relations = [
                rel for rel in relations
                if rel['source'] in display_ids and rel['target'] in display_ids
            ]
            self.graph_widget.set_data(notes_to_display, filtered_relations)
            print(f"Found notes: {found_notes_data}")
            print(f"Display IDs: {display_ids}")
            print(f"Notes to display: {[note['title'] for note in notes_to_display]}")

            print("=== DEBUG: Visualization Data ===")
            print("Notes to display:")
            for note in notes_to_display:
                print(f"  ID: {note['id']}, Title: {note.get('title')}, Parent: {note.get('parent_id')}, Children: {note.get('children')}")
            print("Relations to display:")
            for rel in filtered_relations:
                print(f"  Source: {rel['source']}, Target: {rel['target']}")
            print("===============================")
            # Set current note context if exactly one note was found
            if len(found_notes_data) == 1:
                self.current_note_context = found_notes_data[0]
                print(f"[DEBUG CONTEXT] Set current_note_context to: {self.current_note_context}")
        # Always refresh notes display if notes were updated (created, updated, deleted)
        if response.get("notes_updated"):
            print("[DEBUG] notes_updated detected in response, refreshing notes display.")
            self.refresh_notes_display()
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

    def clear_visualization(self):
        """Clear the visualization graph."""
        self.graph_widget.set_data([], [])

    def start_description_update(self, note_title, update_type):
        self.accumulating_description = True
        self.accumulated_speech = []
        self.pending_update_type = update_type
        self.pending_note_title = note_title
        self.status_label.text = 'Listening for description...'
        self.record_btn.text = 'Recording...'
        self.record_btn.background_color = (0.9, 0.3, 0.3, 1)
        self.stop_btn.disabled = False
        silence_timeout = self.app_instance.config_service.get_silence_timeout()
        recording_timeout = self.app_instance.config_service.get_recording_timeout()
        self.app_instance.speech_service.start_listening(
            on_result=self.on_speech_result,
            on_error=self.on_speech_error,
            on_auto_stop=self.on_auto_stop,
            silence_timeout=silence_timeout,
            recording_timeout=recording_timeout
        )

    def show_welcome_popup(self, message):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        label = Label(text=message, font_size='16sp', halign='right' if self.get_language() == 'he-IL' else 'left', valign='top', size_hint_y=1)
        label.bind(size=label.setter('text_size'))
        btn = Button(text='אישור' if self.get_language() == 'he-IL' else 'OK', size_hint_y=None, height=40)
        layout.add_widget(label)
        layout.add_widget(btn)
        popup = Popup(title='הוראות שימוש' if self.get_language() == 'he-IL' else 'Usage Instructions', content=layout, size_hint=(0.8, 0.8), auto_dismiss=False)
        def on_ok(instance):
            popup.dismiss()
            self.welcome_shown = True
            print('[DEBUG] Welcome popup dismissed, welcome_shown set to True')
        btn.bind(on_release=on_ok)
        print('[DEBUG] Showing welcome popup')
        popup.open() 