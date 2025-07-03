from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp


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
        
        # Notes content placeholder
        content = Label(
            text='Notes history will be displayed here.\n\n'
                  '- Save transcribed text\n'
                  '- View previous notes\n'
                  '- Search through notes\n'
                  '- Export notes\n'
                  '- Delete notes',
            font_size='16sp',
            halign='center',
            valign='middle'
        )
        content.text_size = (None, None)
        
        layout.add_widget(header)
        layout.add_widget(content)
        self.add_widget(layout) 