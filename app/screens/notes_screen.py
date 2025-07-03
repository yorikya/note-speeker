from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import json
from bidi.algorithm import get_display


class NotesScreen(Screen):
    """Notes screen placeholder"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'notes'
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the notes screen UI"""
        layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(20))
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
        
        back_btn = Button(
            text='Back',
            size_hint=(None, 1),
            width=dp(100),
            font_size='16sp'
        )
        back_btn.bind(on_press=lambda x: self.app_instance.show_home_screen())
        
        title = Label(
            text='Notes',
            font_size='20sp',
            bold=True
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        
        # Get notes data as JSON
        nlp_service = self.app_instance.nlp_service
        notes_data = {
            'last_note_id': nlp_service.last_note_id,
            'notes': nlp_service.notes
        }
        notes_json = json.dumps(notes_data, ensure_ascii=False, indent=2)
        notes_json_display = get_display(notes_json)
        # Scrollable, selectable text area
        notes_text = TextInput(
            text=notes_json_display,
            readonly=True,
            font_size='14sp',
            size_hint_y=None,
            height=dp(600),
            background_color=(0.13, 0.15, 0.18, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1),
            font_name='app/fonts/Alef-Regular.ttf',
            multiline=True
        )
        scroll = ScrollView()
        notes_text.bind(minimum_height=notes_text.setter('height'))
        scroll.add_widget(notes_text)
        
        layout.add_widget(header)
        layout.add_widget(scroll)
        self.add_widget(layout) 