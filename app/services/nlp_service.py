import google.generativeai as genai
from typing import Dict, List, Optional
import json
import os
from kivy.utils import platform
import re
import unicodedata
import traceback

class NoteTool:
    """Base class for note management tools"""
    def __init__(self, notes: List[Dict]):
        self.notes = notes

    def run(self, params: Dict) -> Dict:
        raise NotImplementedError

class CreateNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        notes = params['nlp_service'].notes
        title = params.get("title")
        description = params.get("description")
        parent_id = params.get("parent_id")
        nlp_service = params.get("nlp_service")
        if not title:
            title = params.get("original_text", "Untitled")
        if not description:
            description = ""
        is_hebrew = title and any(c > 'z' for c in title)
        # Duplicate detection
        existing_note = next((n for n in notes if n["title"] == title and n["parent_id"] == parent_id), None)
        if existing_note and not params.get('override_confirmed'):
            response = (
                f"רשומה בשם '{title}' כבר קיימת. האם להחליף אותה?" if is_hebrew
                else f"A note with the name '{title}' already exists. Do you want to override it?"
            )
            return {
                "operation": "override_confirm",
                "response": response,
                "requires_confirmation": True,
                "pending_note": {**params, 'override_confirmed': True}
            }
        if existing_note and params.get('override_confirmed'):
            notes.remove(existing_note)
        new_note = {
            "id": str(len(notes) + 1),
            "title": title,
            "description": description,
            "parent_id": parent_id,
            "children": [],
            "done": False,
            "done_date": None,
            "relations": {},
            "links": [],
            "tags": []
        }
        notes.append(new_note)
        print(f"[DEBUG] Added new note: {new_note}")
        print(f"[DEBUG] Notes after creation: {len(notes)}")
        if parent_id:
            parent = next(n for n in notes if n["id"] == parent_id)
            parent["children"].append(new_note["id"])
        print("[DEBUG] CreateNoteTool: calling _save_notes...")
        if nlp_service:
            nlp_service._save_notes()
        response = (
            f'נוצרה רשומה: {title}' if is_hebrew
            else f'Created note: {title}'
        )
        return {
            "operation": "create",
            "response": response,
            "requires_confirmation": False
        }

class UpdateNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        notes = params['nlp_service'].notes
        target_id = params.get("target_id")
        updates = params.get("updates", "")
        is_hebrew = target_id and any(c > 'z' for c in target_id)
        note = next((n for n in notes if n["id"] == target_id), None)
        if not note:
            note = next((n for n in notes if n["title"] == target_id), None)
        if note:
            if isinstance(updates, str):
                current_desc = note.get("description", "")
                if current_desc:
                    note["description"] = current_desc + "\n" + updates
                else:
                    note["description"] = updates
            elif isinstance(updates, dict):
                note.update(updates)
            print(f"[DEBUG] Updated note: {note}")
            print("[DEBUG] UpdateNoteTool: calling _save_notes...")
            nlp_service = params.get("nlp_service")
            if nlp_service:
                nlp_service._save_notes()
            response = (
                f"עודכנה רשומה: {note['title']}" if is_hebrew
                else f"Updated note: {note['title']}"
            )
            return {
                "operation": "update",
                "response": response
            }
        print(f"[DEBUG] Note not found with id/title: {target_id}")
        response = (
            "רשומה לא נמצאה" if is_hebrew
            else "Note not found"
        )
        return {
            "operation": "error",
            "response": response
        }

class DeleteNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        notes = params['nlp_service'].notes
        target_id = params.get("target_id")
        note = next((n for n in notes if n["id"] == target_id), None)
        if note:
            notes.remove(note)
            print(f"[DEBUG] Deleted note: {note}")
            print("[DEBUG] DeleteNoteTool: calling _save_notes...")
            nlp_service = params.get("nlp_service")
            if nlp_service:
                nlp_service._save_notes()
            return {
                "operation": "delete",
                "response": f"Deleted note: {note['title']}"
            }
        print(f"[DEBUG] Note not found with id: {target_id}")
        return {
            "operation": "error",
            "response": "רשומה לא נמצאה" if target_id and any(c > 'z' for c in target_id) else "Note not found"
        }

class FindNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        notes = params['nlp_service'].notes
        query = params.get("query", "")
        is_hebrew = query and any(c > 'z' for c in query)
        matches = []
        for note in notes:
            title = note.get("title") or ""
            desc = note.get("description") or ""
            if is_hebrew:
                if query in title or query in desc:
                    matches.append(note)
            else:
                if query.lower() in title.lower() or query.lower() in desc.lower():
                    matches.append(note)
        print(f"[DEBUG] Found {len(matches)} matches: {matches}")
        response = f"נמצאו {len(matches)} רשומות" if is_hebrew else f"Found {len(matches)} notes"
        return {
            "operation": "find",
            "response": response,
            "matches": matches
        }

class ExtractSubNoteTitleTool:
    def __init__(self):
        pass
    def run(self, params: Dict) -> Dict:
        text = params.get('text', '')
        language = params.get('language', 'en')
        import re
        is_hebrew = language == 'he-IL'
        title = None
        debug_info = {}
        if is_hebrew:
            # Try to extract after 'בשם' or 'השם'
            match = re.search(r"(?:בשם|השם)\s*['\"]?([^'\"]+)['\"]?", text)
            if match:
                title = match.group(1).strip()
            else:
                # Try to extract after 'תוסיף תת רשומה', 'תת רשומה', 'תת-רשומה', etc.
                match = re.search(r"(?:תוסיף\s*)?תת[- ]?רשומה(?: בשם)?\s*['\"]?([^'\"]+)['\"]?", text)
                if match:
                    title = match.group(1).strip()
                else:
                    # Fallback: last word (if not a stopword)
                    words = text.strip().split()
                    if words and len(words) > 2:
                        candidate = words[-1]
                        # Avoid fallback to 'תת', 'רשומה', etc.
                        if candidate not in ["תת", "רשומה", "תת-רשומה"]:
                            title = candidate
        else:
            # Try to extract after 'called', 'named', 'titled'
            match = re.search(r"(?:called|named|titled)\s*['\"]?([^'\"]+)['\"]?", text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
            else:
                # Try to extract after 'sub-note' or 'child note'
                match = re.search(r"(?:sub[- ]?note|child note)\s*(?:called|named|titled)?\s*['\"]?([^'\"]+)['\"]?", text, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                else:
                    # Fallback: last word
                    words = text.strip().split()
                    if words and len(words) > 2:
                        candidate = words[-1]
                        if candidate.lower() not in ["sub-note", "sub", "note", "child", "child-note"]:
                            title = candidate
        debug_info['input'] = text
        debug_info['extracted_title'] = title
        if title:
            return {'title': title, 'success': True, 'debug': debug_info}
        else:
            return {'title': '', 'success': False, 'debug': debug_info, 'response': 'Could not extract sub-note title. Please specify the title.'}

class ConfirmationIntentTool:
    def __init__(self):
        # Define affirmative and negative phrases for both languages
        self.affirmative_he = ["כן", "תוסיף", "צור", "הוסף", "בצע", "אשר", "לך על זה"]
        self.negative_he = ["לא", "בטל", "אל", "לא רוצה", "אל תבצע", "אל תוסיף", "אל תעדכן"]
        self.affirmative_en = ["yes", "add", "create", "go ahead", "do it", "confirm", "okay", "sure"]
        self.negative_en = ["no", "cancel", "don't", "do not", "nope", "stop", "never", "don't do it"]

    def run(self, params: Dict) -> Dict:
        text = params.get('text', '').strip()
        language = params.get('language', 'en')
        import unicodedata
        normalized_text = unicodedata.normalize('NFKC', text.lower())
        is_hebrew = language == 'he-IL'
        if is_hebrew:
            for phrase in self.affirmative_he:
                if phrase in normalized_text:
                    return {'intent': 'yes'}
            for phrase in self.negative_he:
                if phrase in normalized_text:
                    return {'intent': 'no'}
        else:
            for phrase in self.affirmative_en:
                if phrase in normalized_text:
                    return {'intent': 'yes'}
            for phrase in self.negative_en:
                if phrase in normalized_text:
                    return {'intent': 'no'}
        return {'intent': 'ambiguous'}

class NLPService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                print(f"[DEBUG] Error initializing Gemini model: {e}")
                
        # Migrate notes from old location if needed
        self._migrate_notes_if_needed()
        
        # Initialize notes file path and load notes
        self.notes_file = self._get_notes_file_path()
        self.notes = self._load_notes()
        self.conversation_state = None  # Track conversation state
        self.conversation_history = []  # Store recent user/agent messages
        
        # Initialize tools with notes
        self.tools = {
            "create": CreateNoteTool(self.notes),
            "update": UpdateNoteTool(self.notes),
            "delete": DeleteNoteTool(self.notes),
            "find": FindNoteTool(self.notes),
            "extract_sub_note_title": ExtractSubNoteTitleTool(),
            "confirmation_intent": ConfirmationIntentTool()
        }
        
        # Enhanced system prompt for better natural language understanding
        self.tool_selection_prompt = """
You are a note management assistant that helps users manage their notes.
Your job is to understand the user's intent from their natural language input and select the appropriate tool.

Available tools:
1. create - Create a new note
   - Trigger phrases (English): "create", "new", "add", "make", "write", "note down", "remember"
   - Trigger phrases (Hebrew): "צור", "חדש", "הוסף", "כתוב", "רשום", "זכור"
   - Example (English): "add milk to shopping list" -> create note "milk" with parent "shopping list"
   - Example (Hebrew): "הוסף חלב לרשימת קניות" -> create note "חלב" with parent "רשימת קניות"

2. update - Update an existing note
   - Trigger phrases (English): "update", "change", "modify", "edit", "add to", "append"
   - Trigger phrases (Hebrew): "עדכן", "שנה", "ערוך", "הוסף ל"
   - Example (English): "Add 'bring documents' to meeting notes" -> update meeting notes
   - Example (Hebrew): "הוסף 'להביא מסמכים' לפגישה" -> update meeting notes

3. delete - Delete a note
   - Trigger phrases (English): "delete", "remove", "erase"
   - Trigger phrases (Hebrew): "מחק", "הסר"
   - Example (English): "delete the milk note" -> delete note titled "milk"
   - Example (Hebrew): "מחק את הרשומה חלב" -> delete note titled "חלב"

4. find - Find notes
   - Trigger phrases (English): "find", "search", "look for", "where is", "show me"
   - Trigger phrases (Hebrew): "מצא", "חפש", "איפה", "הראה לי", "אני מחפש"
   - Example (English): "Where did I write about the meeting?" -> find notes about meeting
   - Example (Hebrew): "איפה כתבתי על הפגישה?" -> find notes about meeting

For each tool, extract these parameters:
- create: title (required), description (optional), parent_id (optional - use note title to find parent)
- update: target_id (use note title to find target), updates (what to change)
- delete: target_id (use note title to find target)
- find: query (text to search for)

IMPORTANT: When dealing with parent-child relationships:
1. For create tool: if the command mentions adding to an existing note, set that note's title as parent_id
2. For update tool: use the note's title to find it, not its ID
3. Always use the exact title as it appears in the user's command

If the command is not clear or doesn't match any tool's purpose, return "unknown" as the tool.

IMPORTANT: Return ONLY a raw JSON object, with NO markdown formatting, NO code blocks, and NO additional text.
The JSON must be in this exact format:
{
    "tool": "tool_name",
    "params": {tool specific parameters},
    "response": "natural language response in the same language as the input",
    "requires_confirmation": true/false
}
"""

    def _get_notes_file_path(self) -> str:
        """Get the path to the notes.json file in user's home directory"""
        import os
        
        # Get the user's home directory
        if platform == 'android':
            from android.storage import primary_external_storage_path
            home_dir = primary_external_storage_path()
        else:
            home_dir = os.path.expanduser('~')
            
        # Create .note_speaker directory if it doesn't exist
        notes_dir = os.path.join(home_dir, '.note_speaker')
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir)
            print(f"[DEBUG] Created notes directory: {notes_dir}")
            
        # Set path to notes.json file
        file_path = os.path.join(notes_dir, 'notes.json')
        print(f"[DEBUG] Notes file path: {file_path}")
        
        # Create empty notes file if it doesn't exist
        if not os.path.exists(file_path):
            print(f"[DEBUG] Creating new notes file: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'notes': []}, f, ensure_ascii=False, indent=2)
                
        return file_path

    def _load_notes(self) -> List[Dict]:
        try:
            if os.path.exists(self.notes_file):
                print(f"[DEBUG] Loading notes from: {self.notes_file}")
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    notes = data.get('notes', [])
                    print(f"[DEBUG] Loaded {len(notes)} notes")
                    return notes
            else:
                print(f"[DEBUG] Notes file does not exist: {self.notes_file}")
        except Exception as e:
            print(f"[DEBUG] Error loading notes: {e}")
        return []

    def _save_notes(self):
        import os
        print(f"[DEBUG] _save_notes called. File: {self.notes_file}")
        # Log file contents before saving
        if os.path.exists(self.notes_file):
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                before = f.read()
            print(f"[DEBUG] notes.json BEFORE save:\n{before}")
        else:
            print("[DEBUG] notes.json does not exist before save.")
        print(f"[DEBUG] Saving {len(self.notes)} notes to: {self.notes_file}")
        with open(self.notes_file, 'w', encoding='utf-8') as f:
            import json
            json.dump({'notes': self.notes}, f, ensure_ascii=False, indent=2)
        # Log file contents after saving
        with open(self.notes_file, 'r', encoding='utf-8') as f:
            after = f.read()
        print(f"[DEBUG] notes.json AFTER save:\n{after}")
        print("[DEBUG] Notes saved successfully")

    def get_relations(self) -> List[Dict]:
        """Get relationships between notes for graph visualization."""
        relations = []
        for note in self.notes:
            if note.get("parent_id"):
                relations.append({"source": note["parent_id"], "target": note["id"]})
        return relations

    def process_command(self, text: str, language: str = 'en') -> Dict:
        print(f"[DEBUG NLP] process_command called with text: '{text}', language: {language}, conversation_state: {self.conversation_state}")
        print(f"[DEBUG NLP] re module id: {id(re) if 're' in globals() else 'NOT FOUND'}")
        # Add to conversation history
        self.conversation_history.append({'role': 'user', 'text': text, 'language': language})
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        print(f"[DEBUG NLP] Raw text repr: {repr(text)}")
        # Normalize text for robust matching
        normalized_text = unicodedata.normalize('NFKC', text.strip())
        # --- Handle multi-turn state for update/delete/add_sub_note after find ---
        if self.conversation_state and self.conversation_state.get('pending_action'):
            print(f"[DEBUG NLP] In pending_action state: {self.conversation_state}")
            is_hebrew = language == 'he-IL'
            found_note = self.conversation_state['found_note']
            action = None
            print(f"[DEBUG NLP] About to check action for text: {text}")
            # Use ConfirmationIntentTool
            intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language})
            print(f"[DEBUG NLP] ConfirmationIntentTool result: {intent_result}")
            is_yes = intent_result['intent'] == 'yes'
            is_no = intent_result['intent'] == 'no'
            print(f"[DEBUG NLP] is_yes: {is_yes}, is_no: {is_no}")
            if is_no:
                self.conversation_state = None
                print(f"[DEBUG NLP] User cancelled action (early exit for 'no').")
                self.conversation_history.append({'role': 'agent', 'text': 'OK, I\'ve cancelled the action.' if not is_hebrew else 'בסדר, ביטלתי את הפעולה.', 'language': language})
                return {'response': "בסדר, ביטלתי את הפעולה." if is_hebrew else "OK, I've cancelled the action."}
            # Only check for action if not is_no
            # Detect sub-note creation
            if (is_hebrew and ("תת" in text or "תת-רשומה" in text or "הוסף תת" in text or "הוסף תת-רשומה" in text)) or (not is_hebrew and ("sub-note" in text.lower() or "sub note" in text.lower() or "child note" in text.lower() or "add sub" in text.lower())):
                action = 'add_sub_note'
            elif (is_hebrew and ("עדכן" in text or "תעדכן" in text)) or (not is_hebrew and ("update" in text.lower() or "edit" in text.lower() or "change" in text.lower() or "modify" in text.lower())):
                action = 'update'
            elif (
                (is_hebrew and any(phrase in text for phrase in ["מחק", "מוחק", "תמחק", "תמחק אותה", "מחק אותה", "מחק את זה", "תמחק את זה"]))
                or (not is_hebrew and any(word in text.lower() for word in ["delete", "remove", "erase", "delete it", "remove it"]))
            ):
                action = 'delete'
            print(f"[DEBUG NLP] Detected action: {action}")
            if action == 'add_sub_note':
                # Use ExtractSubNoteTitleTool to get the sub-note title
                extract_result = self.tools['extract_sub_note_title'].run({'text': text, 'language': language, 'history': self.conversation_history})
                print(f"[DEBUG NLP] ExtractSubNoteTitleTool result: {extract_result}")
                sub_title = extract_result.get('title', '').strip()
                if not extract_result.get('success') or not sub_title:
                    response = extract_result.get('response', 'Could not extract sub-note title. Please specify the title.')
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {'response': response, 'requires_confirmation': True}
                # Ask for confirmation before creating sub-note
                self.conversation_state = {
                    'operation': 'create',
                    'pending_note': {
                        'title': sub_title,
                        'parent_id': found_note['id'],
                        'requires_confirmation': True,
                        'nlp_service': self
                    },
                    'confirm_action': 'add_sub_note',
                    'found_note': found_note
                }
                response = (
                    f"להוסיף תת-רשומה בשם {sub_title} תחת {found_note['title']}?" if is_hebrew
                    else f"Add a sub-note called {sub_title} under {found_note['title']}?"
                )
                print(f"[DEBUG NLP] Returning add sub-note confirmation: {response}")
                self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                return {'response': response, 'requires_confirmation': True}
            elif action == 'update':
                print(f"[DEBUG NLP] About to use re for update extraction. re id: {id(re) if 're' in globals() else 'NOT FOUND'}")
                # For Hebrew, look for 'עדכן את התוכן ל-' or similar
                if is_hebrew:
                    match = re.search(r"עדכן(?:\s+את)?(?:\s+התוכן)?(?:\s+ל|-)?\s*(.*)", text)
                else:
                    match = re.search(r"update(?:\s+the)?(?:\s+content)?(?:\s+to|-)?\s*(.*)", text, re.IGNORECASE)
                new_content = match.group(1).strip() if match and match.group(1) else text
                print(f"[DEBUG NLP] Extracted new_content: {new_content}")
                # Ask for confirmation before updating
                self.conversation_state = {
                    'operation': 'update',
                    'pending_note': {
                        'target_id': found_note['title'],
                        'updates': new_content,
                        'requires_confirmation': True
                    },
                    'confirm_action': 'update',
                    'found_note': found_note
                }
                response = (
                    f"לעדכן את התוכן של {found_note['title']} ל- {new_content}. האם לאשר?" if is_hebrew
                    else f"Update the content of {found_note['title']} to: {new_content}. Confirm?"
                )
                print(f"[DEBUG NLP] Returning update confirmation: {response}")
                self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                return {'response': response, 'requires_confirmation': True}
            elif action == 'delete':
                print(f"[DEBUG NLP] About to ask for delete confirmation.")
                self.conversation_state = {
                    'operation': 'delete',
                    'pending_note': {
                        'target_id': found_note['title'],
                        'requires_confirmation': True
                    },
                    'confirm_action': 'delete',
                    'found_note': found_note
                }
                response = (
                    f"האם למחוק את הרשומה {found_note['title']}?" if is_hebrew
                    else f"Delete the note {found_note['title']}?"
                )
                print(f"[DEBUG NLP] Returning delete confirmation: {response}")
                self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                return {'response': response, 'requires_confirmation': True}
            elif is_yes and self.conversation_state.get('confirm_action'):
                operation = self.conversation_state['operation']
                pending_note = self.conversation_state['pending_note']
                print(f"[DEBUG NLP] Confirmation received: is_yes={is_yes}, operation={operation}, pending_note={pending_note}")
                pending_note['requires_confirmation'] = False
                # Ensure nlp_service is present for all operations
                if 'nlp_service' not in pending_note:
                    pending_note['nlp_service'] = self
                print(f"[DEBUG NLP] pending_note before tool call: {pending_note}")
                print(f"[DEBUG NLP] About to call tool '{operation}' with pending_note: {pending_note}")
                tool = self.tools.get(operation)
                if tool:
                    result = tool.run(pending_note)
                    result['notes_updated'] = True
                else:
                    result = {'response': 'Error: Tool not found.'}
                self.conversation_state = None
                print(f"[DEBUG NLP] Returning result after confirmation: {result}")
                self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                return result
            response = (
                "אנא ציין אם ברצונך לעדכן, למחוק או להוסיף תת-רשומה, או אשר/בטל." if is_hebrew
                else "Please specify if you want to update, delete, or add a sub-note, or confirm/cancel."
            )
            print(f"[DEBUG NLP] Returning ambiguous action response: {response}")
            self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
            return {'response': response, 'requires_confirmation': True}
        # --- Existing confirmation state for update/delete ---
        if self.conversation_state:
            print(f"[DEBUG NLP] In conversation state: {self.conversation_state}")
            is_hebrew = language == 'he-IL'
            # Use ConfirmationIntentTool
            intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language})
            print(f"[DEBUG NLP] ConfirmationIntentTool result: {intent_result}")
            is_yes = intent_result['intent'] == 'yes'
            if is_yes:
                print("[DEBUG NLP] User confirmed.")
                operation = self.conversation_state.get("operation")
                pending_note = self.conversation_state.get("pending_note")
                pending_note["requires_confirmation"] = False
                # Ensure nlp_service is present for all operations
                if 'nlp_service' not in pending_note:
                    pending_note['nlp_service'] = self
                print(f"[DEBUG NLP] pending_note before tool call: {pending_note}")
                tool = self.tools.get(operation)
                if tool:
                    result = tool.run(pending_note)
                    result["notes_updated"] = True
                else:
                    result = {"response": "Error: Tool not found."}
                self.conversation_state = None
                print(f"[DEBUG NLP] Returning result after confirmation: {result}")
                self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                return result
            else:
                print("[DEBUG NLP] User denied.")
                self.conversation_state = None
                result = {
                    "response": "בסדר, ביטלתי את הפעולה." if is_hebrew else "OK, I've cancelled the action."
                }
            print(f"[DEBUG NLP] Result after confirmation: {result}")
            self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
            return result

        # --- Tool selection and normal flow ---
        try:
            print("[DEBUG NLP] Performing tool selection via Gemini...")
            # Build chat history string for context
            history_str = ""
            for msg in self.conversation_history[-5:]:  # last 5 turns
                prefix = "User:" if msg['role'] == 'user' else "Agent:"
                history_str += f"{prefix} {msg['text']}\n"
            # Add the current user message
            history_str += f"User: {text}\n"
            # Pass chat history + tool selection prompt to the model
            response = self.model.generate_content(history_str + self.tool_selection_prompt)
            tool_call_match = re.search(r"```json\s*(\{.*?\})\s*```", response.text, re.DOTALL)
            if tool_call_match:
                tool_call_str = tool_call_match.group(1)
                print(f"[DEBUG NLP] Extracted tool call: {tool_call_str}")
                tool_call = json.loads(tool_call_str)
                tool_name = tool_call.get("tool")
                params = tool_call.get("params", {})
                params["original_text"] = text
                if tool_name == 'find':
                    params["nlp_service"] = self
                    # Intercept find result for 1 note
                    result = self.tools[tool_name].run(params)
                    matches = result.get('matches', [])
                    is_hebrew = language == 'he-IL'
                    if len(matches) == 1:
                        # Set pending_action state
                        self.conversation_state = {
                            'pending_action': True,
                            'found_note': matches[0]
                        }
                        response = (
                            f"נמצאה רשומה אחת. האם תרצה לעדכן, למחוק או להוסיף תת-רשומה?" if is_hebrew
                            else "Found 1 note. Would you like to update, delete, or add a sub-note?"
                        )
                        return {
                            'response': response,
                            'matches': matches,
                            'requires_confirmation': True
                        }
                    else:
                        return result
                if tool_name in self.tools:
                    print(f"[DEBUG NLP] Executing tool: '{tool_name}' with params: {params}")
                    params["nlp_service"] = self
                    result = self.tools[tool_name].run(params)
                    if result.get("requires_confirmation"):
                        self.conversation_state = {
                            "operation": tool_name,
                            "pending_note": params
                        }
                        print(f"[DEBUG NLP] Stored conversation state for confirmation: {self.conversation_state}")
                    else:
                        result["notes_updated"] = True
                else:
                    print(f"[DEBUG NLP] Tool '{tool_name}' not found.")
                    result = {"response": "I'm not sure how to do that."}
            else:
                print("[DEBUG NLP] No tool call found in Gemini response.")
                result = {"response": response.text}
        except Exception as e:
            print(f"[DEBUG NLP] Error during NLP processing: {e}")
            result = {
                "response": "I had trouble understanding that. Please try again."
            }
        print(f"[DEBUG NLP] Final result: {result}")
        self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
        return result

    def _migrate_notes_if_needed(self):
        """Migrate notes from old location (project root) to new location (~/.note_speaker)"""
        import os
        
        # Get old notes file path (project root)
        old_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'notes.json'
        )
        
        # If old notes file exists, migrate its contents
        if os.path.exists(old_path):
            try:
                print(f"[DEBUG] Found old notes file at {old_path}")
                with open(old_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    
                # Get new file path
                new_path = self._get_notes_file_path()
                
                # If new file is empty, copy old notes
                if os.path.exists(new_path):
                    with open(new_path, 'r', encoding='utf-8') as f:
                        new_data = json.load(f)
                        if not new_data.get('notes'):
                            print(f"[DEBUG] Migrating notes to new location: {new_path}")
                            with open(new_path, 'w', encoding='utf-8') as f2:
                                json.dump(old_data, f2, ensure_ascii=False, indent=2)
                
                # Delete old notes file
                os.remove(old_path)
                print(f"[DEBUG] Deleted old notes file after migration")
                
            except Exception as e:
                print(f"[DEBUG] Error during notes migration: {e}") 