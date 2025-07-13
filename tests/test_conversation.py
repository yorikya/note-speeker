import unittest
import tempfile
import os
import time
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
        response = self.nlp.process_command("כן", language="he-IL")
        update_response = response.get("response", "")
        # self.assertIn("עודכנה רשומה", update_response, f"Agent did not confirm update: {update_response}")
        print("response (update applied):", response)

        # Step 5: Check that the note's description was updated
        note = next((n for n in self.nlp.notes if "רשימת קניות" in n['title']), None)
        self.assertIsNotNone(note)
        self.assertIn(description, note['description'])

    def test_create_subnote_hebrew(self):
        """
        Scenario: User creates a note and then creates a sub-note (child note) for it in Hebrew, using a multi-turn, context-aware flow.
        Flow:
        1. User creates a note called 'רשימת קניות'.
        2. User finds the note ('תמצא רשימת קניות').
        3. Agent responds with a context prompt (e.g., 'נמצאה רשומה אחת. האם תרצה לעדכן...').
        4. User says 'הוסף תת רשומה חלב' (add a sub-note called 'חלב').
        5. Agent prompts for confirmation to create the sub-note.
        6. User confirms ('כן').
        7. Agent creates the sub-note and confirms.
        8. Test checks that the sub-note exists and is linked to the parent note.
        """
        # Step 0: Create the parent note first
        response = self.nlp.process_command("צור רשימת קניות", language="he-IL")
        response = self.nlp.process_command("כן", language="he-IL")

        # Step 1: User finds the parent note
        response = self.nlp.process_command("תמצא רשימת קניות", language="he-IL")
        found_response = response.get("response", "")
        self.assertTrue(
            "נמצאו" in found_response or "נמצאה רשומה אחת" in found_response,
            f"Unexpected agent response: {found_response}"
        )

        # Step 2: User requests to add a sub-note called 'חלב'
        response = self.nlp.process_command("הוסף תת רשומה חלב", language="he-IL")
        subnote_prompt = response.get("response", "")
        self.assertIn("האם להוסיף תת-רשומה", subnote_prompt, f"Agent did not prompt for sub-note confirmation: {subnote_prompt}")
        print("response (prompt for sub-note confirmation):", response)

        # Step 3: User confirms the sub-note creation
        response = self.nlp.process_command("כן", language="he-IL")
        subnote_response = response.get("response", "")
        self.assertIn("נוצרה רשומה", subnote_response, f"Agent did not confirm sub-note creation: {subnote_response}")
        print("response (sub-note created):", response)

        # Step 4: Check that the sub-note exists and is linked to the parent
        parent_note = next((n for n in self.nlp.notes if "רשימת קניות" in n['title']), None)
        self.assertIsNotNone(parent_note)
        subnote = next((n for n in self.nlp.notes if n['title'] == 'חלב' and n.get('parent_id') == parent_note['id']), None)
        self.assertIsNotNone(subnote, "Sub-note 'חלב' was not created or not linked to parent note.")
        self.assertIn(subnote['id'], parent_note['children'], "Sub-note ID not found in parent's children list.")

    def test_delete_note_hebrew(self):
        """
        Scenario: User creates a note, finds it, and deletes it in Hebrew, using a multi-turn, context-aware flow.
        After deletion, a find should return.
        """
        # Step 0: Create the note first
        response = self.nlp.process_command("צור רשימת קניות", language="he-IL")
        print("response (create note):", response)
        response = self.nlp.process_command("כן", language="he-IL")
        print("response (confirm create note):", response)

        # Step 1: User finds the note
        response = self.nlp.process_command("תמצא רשימת קניות", language="he-IL")
        found_response = response.get("response", "")
        self.assertIn("נמצאה רשומה אחת", found_response)

        # Step 2: User requests to delete the note
        response = self.nlp.process_command("מחק", language="he-IL")
        delete_prompt = response.get("response", "")
        self.assertIn("האם למחוק", delete_prompt, f"Agent did not prompt for delete confirmation: {delete_prompt}")
        print("response (prompt for delete confirmation):", response)

        # Step 3: User confirms the deletion
        response = self.nlp.process_command("כן", language="he-IL")
        delete_response = response.get("response", "")
        # The agent may not return a direct confirmation, so check by searching for the note
        print("response (note deleted):", response)
        response = self.nlp.process_command("תמצא רשימת קניות", language="he-IL")
        not_found_response = response.get("response", "")
        print("response (note not found):", response)
        self.assertIn("נמצאו 0 רשומות", not_found_response, f"Agent did not confirm deletion: {not_found_response}")
        note = next((n for n in self.nlp.notes if "רשימת קניות" in n['title']), None)
        self.assertIsNone(note, "Note was not deleted.")

    def test_update_description_append_hebrew(self):
        """
        Scenario: User updates a note's description in Hebrew by sending multiple update messages, each appended to the description.
        After each update, context is lost, so the note must be re-found before the next update.
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

        # First update
        response = self.nlp.process_command("עדכן תיאור של הרשומה", language="he-IL")
        update_prompt = response.get("response", "")
        self.assertIn("לעדכן", update_prompt, f"Agent did not prompt for update content: {update_prompt}")
        part1 = "רשומה זאת משמשת לשמור רשימת קניות שבועית"
        response = self.nlp.process_command(part1, language="he-IL")
        confirm_prompt = response.get("response", "")
        self.assertIn("לעדכן", confirm_prompt, f"Agent did not ask for update confirmation: {confirm_prompt}")
        response = self.nlp.process_command("כן", language="he-IL")
        update_response = response.get("response", "")
        print("response (first update applied):", response)

        # After update, context is lost, so re-find the note before next update
        response = self.nlp.process_command("תמצא רשימת קניות", language="he-IL")
        found_response2 = response.get("response", "")
        self.assertTrue(
            "נמצאו" in found_response2 or "נמצאה רשומה אחת" in found_response2,
            f"Unexpected agent response: {found_response2}"
        )

        # Second update
        response = self.nlp.process_command("עדכן תיאור של הרשומה", language="he-IL")
        update_prompt2 = response.get("response", "")
        self.assertIn("לעדכן", update_prompt2, f"Agent did not prompt for update content: {update_prompt2}")
        part2 = "נא להוסיף ירקות ופירות"
        response = self.nlp.process_command(part2, language="he-IL")
        confirm_prompt2 = response.get("response", "")
        self.assertIn("לעדכן", confirm_prompt2, f"Agent did not ask for update confirmation: {confirm_prompt2}")
        response = self.nlp.process_command("כן", language="he-IL")
        update_response2 = response.get("response", "")
        print("response (second update applied):", response)

        # Check that the note's description contains both parts, concatenated
        note = next((n for n in self.nlp.notes if "רשימת קניות" in n['title']), None)
        self.assertIsNotNone(note)
        self.assertIn(part1, note['description'])
        self.assertIn(part2, note['description'])

if __name__ == "__main__":
    unittest.main() 