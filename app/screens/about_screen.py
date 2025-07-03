from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from bidi.algorithm import get_display


class HelpScreen(Screen):
    """Help screen (formerly About)"""
    
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app_instance = app_instance
        self.name = 'help'
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the help screen UI"""
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
            text='Help',
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        
        # Combined instructions (English + Hebrew)
        usage_en = (
            "Note Speaker v1.0\n"
            "A speech-to-text application built with Kivy.\n\n"
            "BASIC COMMANDS:\n"
            "Create a note: 'create note shopping list'\n"
            "Update a note: 'update note groceries'\n"
            "Delete a note: 'delete note groceries'\n"
            "Add a sub-note: 'add sub-note called oil change'\n"
            "Find a note: 'find note groceries'\n"
            "After finding a note, you can say: 'delete', 'update', 'add sub-note', etc.\n\n"
            "ADVANCED COMMANDS (first find a note, then perform the action):\n"
            "To use advanced commands like updating description, adding a tag, or marking as done, first find the note you want to work with.\n\n"
            "Add to description: 'add to note groceries: get bread'\n"
            "Add a tag: 'add tag urgent to note shopping list'\n"
            "Mark as done: 'mark note as done'\n\n"
            "The app will always ask for confirmation before creating or deleting notes.\n"
            "Say 'yes' or 'no' to confirm or cancel actions.\n\n"
            "You can change this setting in the Settings window.\n"
        )
        usage_he = (
            "!Note Speaker ברוכים הבאים ל-\n"
            "ניתן לשלוט באפליקציה באמצעות קולכם. הנה דוגמאות:\n\n"
            "פקודות בסיסיות:\n"
            "יצירת רשומה: 'תיצור רשומה רשימת קניות'\n"
            "עדכון רשומה: 'עדכן רשומה חלב'\n"
            "מחיקת רשומה: 'מחק רשומה חלב'\n"
            "הוספת תת-רשומה: 'תוסיף תת רשומה לעשות טסט'\n"
            "חיפוש רשומה: 'תמצא רשומה חלב'\n"
            "לאחר שמצאת רשומה, אפשר לומר: 'מחק', 'עדכן', 'הוסף תת רשומה' וכו'.\n\n"
            "פקודות מתקדמות (יש למצוא רשומה קודם):\n"
            "כדי להשתמש בפקודות מתקדמות כמו עדכון תיאור, הוספת תג או סימון כהושלמה, יש קודם למצוא/לבחור את הרשומה הרצויה.\n\n"
            "הוספת תוכן לתיאור: 'הוסף לרשומה חלב: לקנות לחם'\n"
            "הוספת תג: 'הוסף תג דחוף לרשומה רשימת קניות'\n"
            "סימון כהושלמה: 'סמן רשומה כהושלמה'\n\n"
            "האפליקציה תמיד תבקש ממך אישור לפני יצירה או מחיקה של רשומות.\n"
            "אמור 'כן' או 'לא' כדי לאשר או לבטל פעולות.\n\n"
            "ניתן לשנות הגדרה זו בחלון ההגדרות.\n"
        )
        # Use the same logic as chat for Hebrew
        usage_he_display = get_display(usage_he)
        # Combine with a separator
        combined = usage_en + "\n" + ("-" * 60) + "\n" + usage_he_display
        # Scrollable content
        scroll = ScrollView()
        help_label = Label(
            text=combined,
            font_size='16sp',
            color=(1, 1, 1, 1),
            halign='left',
            valign='top',
            font_name='app/fonts/Alef-Regular.ttf',  # Use Hebrew-friendly font for all
            size_hint_y=None
        )
        help_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        help_label.text_size = (900, None)
        # Add a dark background to the label
        with help_label.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.15, 0.18, 0.22, 1)
            help_label.bg_rect = RoundedRectangle(size=help_label.size, pos=help_label.pos, radius=[10])
            help_label.bind(size=lambda instance, value: setattr(help_label.bg_rect, 'size', value))
            help_label.bind(pos=lambda instance, value: setattr(help_label.bg_rect, 'pos', value))
        scroll.add_widget(help_label)
        layout.add_widget(header)
        layout.add_widget(scroll)
        self.add_widget(layout) 