import unittest
import tempfile
import os
from app.services.nlp_service import NLPService

class TestConversationHebrewFindAndUpdateDescription(unittest.TestCase):
    def setUp(self):
        self.temp_notes_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_notes_file.close()
        temp_file_name = self.temp_notes_file.name
        NLPService._get_notes_file_path = lambda self: temp_file_name
        self.nlp = NLPService(api_key=None)
        self.nlp.notes = []
        self.nlp.last_note_id = 0
        self.nlp._save_notes()

    def tearDown(self):
        os.unlink(self.temp_notes_file.name)

    def test_find_and_update_description_hebrew(self):
        """
        Scenario: User finds a note and updates its description in Hebrew, using a multi-turn, context-aware flow.
        Flow:
        1. User creates a note called 'רשימת קניות'.
        2. User finds the note ('תמצא רשימת קניות').
        3. Agent responds with a context prompt (e.g., 'נמצאה רשומה אחת. האם תרצה לעדכן...').
        4. User says 'עדכן תיאור של הרשומה' (update the note's description).
        5. Agent prompts for the new content.
        6. User provides the new description.
        7. Agent asks for confirmation to update.
        8. User confirms ('כן תעדכן').
        9. Agent updates the note and confirms.
        10. Test checks that the note's description was updated.
        """
        # Step 0: Create the note first
        response = self.nlp.process_command("צור רשימת קניות", language="he-IL")
        response = self.nlp.process_command("כן", language="he-IL")

        # Step 1: User finds the note
        response = self.nlp.process_command("תמצא רשימת קניות", language="he-IL")
        found_response = response.get("response", "")
        self.assertTrue(
            "נמצאו" in found_response or "נמצאה רשומה אחת" in found_response,
            f"Unexpected agent response: {found_response}"
        )

        # Step 2: User requests to update the note's description
        response = self.nlp.process_command("עדכן תיאור של הרשומה", language="he-IL")
        update_prompt = response.get("response", "")
        self.assertIn("לעדכן", update_prompt, f"Agent did not prompt for update content: {update_prompt}")
        print("response (prompt for update content):", response)

        # Step 3: User provides the new description
        description = "רשומה זאת משמשת לשמור רשימת קניות שבועית"
        response = self.nlp.process_command(description, language="he-IL")
        confirm_prompt = response.get("response", "")
        self.assertIn("לעדכן", confirm_prompt, f"Agent did not ask for update confirmation: {confirm_prompt}")
        print("response (prompt for update confirmation):", response)

        # Step 4: User confirms the update
        response = self.nlp.process_command("כן תעדכן", language="he-IL")
        update_response = response.get("response", "")
        self.assertIn("עודכנה רשומה", update_response, f"Agent did not confirm update: {update_response}")
        print("response (update applied):", response)

        # Step 5: Check that the note's description was updated
        note = next((n for n in self.nlp.notes if "רשימת קניות" in n['title']), None)
        self.assertIsNotNone(note)
        self.assertIn(description, note['description'])

if __name__ == "__main__":
    unittest.main() 