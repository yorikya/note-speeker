import unittest
from app.services.nlp_service import NLPService

class TestConversationE2E(unittest.TestCase):
    def setUp(self):
        # Use a fresh NLPService for each test
        self.nlp = NLPService(api_key=None)
        self.nlp.notes = []
        self.nlp.last_note_id = 0

    def test_create_note_english(self):
        response = self.nlp.process_command("create note shopping list", language="en")
        self.assertIn("create", response.get("operation", "") or response.get("tool", ""))
        self.assertIn("create", response.get("response", "").lower())
        # Confirm creation
        response2 = self.nlp.process_command("yes", language="en")
        self.assertIn("created", response2.get("response", "").lower())

    def test_create_note_hebrew(self):
        response = self.nlp.process_command("צור רשימת קניות", language="he-IL")
        self.assertIn("צור", response.get("operation", "") or response.get("tool", ""))
        self.assertIn("רשומה חדשה", response.get("response", ""))
        # Confirm creation
        response2 = self.nlp.process_command("כן", language="he-IL")
        self.assertIn("עודכן", response2.get("response", "") or response2.get("response", ""))

    def test_update_note_english(self):
        # Create first
        self.nlp.process_command("create note groceries", language="en")
        self.nlp.process_command("yes", language="en")
        # Update
        response = self.nlp.process_command("update note groceries", language="en")
        self.assertIn("update", response.get("operation", "") or response.get("tool", ""))

    def test_update_note_hebrew(self):
        self.nlp.process_command("צור רשימת קניות", language="he-IL")
        self.nlp.process_command("כן", language="he-IL")
        response = self.nlp.process_command("עדכן רשימת קניות", language="he-IL")
        self.assertIn("עדכן", response.get("operation", "") or response.get("tool", ""))

    def test_delete_note_english(self):
        self.nlp.process_command("create note groceries", language="en")
        self.nlp.process_command("yes", language="en")
        response = self.nlp.process_command("delete note groceries", language="en")
        self.assertIn("delete", response.get("operation", "") or response.get("tool", ""))

    def test_delete_note_hebrew(self):
        self.nlp.process_command("צור רשימת קניות", language="he-IL")
        self.nlp.process_command("כן", language="he-IL")
        response = self.nlp.process_command("מחק רשימת קניות", language="he-IL")
        self.assertIn("מחק", response.get("operation", "") or response.get("tool", ""))

    def test_update_description_english(self):
        self.nlp.process_command("create note groceries", language="en")
        self.nlp.process_command("yes", language="en")
        self.nlp.process_command("find note groceries", language="en")
        response = self.nlp.process_command("update description: this is my weekly list", language="en")
        self.assertIn("update", response.get("operation", "") or response.get("tool", ""))

    def test_update_description_hebrew(self):
        self.nlp.process_command("צור רשימת קניות", language="he-IL")
        self.nlp.process_command("כן", language="he-IL")
        self.nlp.process_command("מצא רשימת קניות", language="he-IL")
        response = self.nlp.process_command("עדכן תיאור: זאת רשימה שבועית", language="he-IL")
        self.assertIn("עדכן", response.get("operation", "") or response.get("tool", ""))

    def test_add_sub_note_english(self):
        self.nlp.process_command("create note groceries", language="en")
        self.nlp.process_command("yes", language="en")
        self.nlp.process_command("find note groceries", language="en")
        response = self.nlp.process_command("add sub-note called milk", language="en")
        self.assertIn("sub-note", response.get("response", "").lower())

    def test_add_sub_note_hebrew(self):
        self.nlp.process_command("צור רשימת קניות", language="he-IL")
        self.nlp.process_command("כן", language="he-IL")
        self.nlp.process_command("מצא רשימת קניות", language="he-IL")
        response = self.nlp.process_command("הוסף תת רשומה חלב", language="he-IL")
        self.assertIn("תת רשומה", response.get("response", ""))

if __name__ == "__main__":
    unittest.main() 