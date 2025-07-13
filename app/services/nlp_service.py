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
    def __init__(self, notes: List[Dict], nlp_service):
        super().__init__(notes)
        self.nlp_service = nlp_service

    def run(self, params: Dict) -> Dict:
        notes = self.nlp_service.notes
        title = params.get("title")
        description = params.get("description")
        parent_id = params.get("parent_id")
        nlp_service = params.get("nlp_service", self.nlp_service)
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
        # Assign a new unique ID
        nlp_service.last_note_id += 1
        new_note = {
            "id": str(nlp_service.last_note_id),
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
        update_type = params.get("update_type", "field_update")
        is_hebrew = target_id and any(c > 'z' for c in target_id)
        note = next((n for n in notes if n["id"] == target_id), None)
        if not note:
            note = next((n for n in notes if n["title"] == target_id), None)
        if note:
            if update_type == "replace_description":
                note["description"] = updates
            elif update_type == "append_description":
                current_desc = note.get("description", "")
                if current_desc:
                    note["description"] = current_desc + "\n" + updates
                else:
                    note["description"] = updates
            elif update_type == "field_update":
                if isinstance(updates, dict):
                    note.update(updates)
                elif isinstance(updates, str):
                    # fallback: append to description
                    current_desc = note.get("description", "")
                    if current_desc:
                        note["description"] = current_desc + "\n" + updates
                    else:
                        note["description"] = updates
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
        if not note:
            note = next((n for n in notes if n["title"] == target_id), None)
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
    def extract_search_term(self, query):
        # Remove all known Hebrew prefixes from the start, repeatedly
        while True:
            new_query = re.sub(r'^(תמצא(י|ו)?|רשימה|רשומה)\s+', '', query)
            if new_query == query:
                break
            query = new_query
        # English: remove leading 'find', 'note', 'list' repeatedly
        while True:
            new_query = re.sub(r'^(find|note|list)\s+', '', query, flags=re.IGNORECASE)
            if new_query == query:
                break
            query = new_query
        return query.strip()

    def run(self, params: Dict) -> Dict:
        notes = params['nlp_service'].notes
        query = params.get("query", "")
        orig_query = query
        query = self.extract_search_term(query)
        is_hebrew = query and any(c > 'z' for c in query)
        matches = []
        print(f"[DEBUG FIND] Original Query: {orig_query} | Extracted: {query}")
        # 1. Try exact title match first
        for note in notes:
            title = note.get("title") or ""
            if title == query:
                print(f"[DEBUG FIND] -> Exact title match!")
                matches.append(note)
        # 2. If no exact match, fallback to substring match
        if not matches:
            for note in notes:
                title = note.get("title") or ""
                desc = note.get("description") or ""
                print(f"[DEBUG FIND] Checking note: title='{title}', desc='{desc}'")
                if is_hebrew:
                    if query in title or query in desc:
                        print(f"[DEBUG FIND] -> Matched (hebrew, substring)!")
                        matches.append(note)
                else:
                    if query.lower() in title.lower() or query.lower() in desc.lower():
                        print(f"[DEBUG FIND] -> Matched (en, substring)!")
                        matches.append(note)
        print(f"[DEBUG] Found {len(matches)} matches: {matches}")
        response = f"נמצאו {len(matches)} רשומות" if is_hebrew else f"Found {len(matches)} notes"
        if len(matches) == 1:
            print(f"[DEBUG CONTEXT] Switching context to note: {matches[0]}")
            self.conversation_state = {'current_note': matches[0]}
            response_text = (
                "נמצאה רשומה אחת. האם תרצה לעדכן, למחוק או להוסיף תת-רשומה?"
                if is_hebrew
                else "Found 1 note. Would you like to update, delete, or add a sub-note?"
            )
            return {
                "response": response_text,
                "matches": matches,
                "requires_confirmation": True
            }
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
        operation = params.get('pending_action', None)  # Pass this from process_command if available
        normalized_text = unicodedata.normalize('NFKC', text.lower())
        is_hebrew = language == 'he-IL'
        if is_hebrew:
            # Special: if pending action is delete, treat more delete phrases as yes
            if operation == 'delete':
                delete_confirm_phrases = [
                    "תמחק", "מחק", "כן תמחק", "כן מחק", "כן",
                    "תמחק רשומה", "מחק רשומה", "כן תמחק רשומה", "כן מחק רשומה"
                ]
                for phrase in delete_confirm_phrases:
                    if phrase in normalized_text:
                        return {'intent': 'yes'}
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
        self.notes, self.last_note_id = self._load_notes_and_last_id()
        self.conversation_state = None  # Track conversation state
        self.conversation_history = []  # Store recent user/agent messages
        
        # Initialize tools with notes
        self.tools = {
            "create": CreateNoteTool(self.notes, self),
            "update": UpdateNoteTool(self.notes),
            "delete": DeleteNoteTool(self.notes),
            "find": FindNoteTool(self.notes),
            "extract_sub_note_title": ExtractSubNoteTitleTool(),
            "confirmation_intent": ConfirmationIntentTool()
        }
        
        # Enhanced system prompt for better natural language understanding
        self.tool_selection_prompt = """
You are a note management assistant that helps users find, update, and delete notes in a very consistent, context-aware way. You always respond in relation to the current note context, and your actions are always tied to the note currently in focus unless the user explicitly switches context by searching for another note.

Your job is to understand the user's intent from their natural language input and select the appropriate tool.

Available tools:
1. create - Create a new note
   - Trigger phrases (English): "create", "new", "add", "make", "write", "note down", "remember"
   - Trigger phrases (Hebrew): "צור", "חדש", "הוסף", "כתוב", "רשום", "זכור", "תיצור", "תיצרי", "תיצרו"
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
- update: target_id (use note id to find target), updates (what to change)
- delete: target_id (use note id to find target)
- find: query (text to search for)

IMPORTANT: When dealing with parent-child relationships:
1. For create tool: if the command mentions adding to an existing note, set that note's title as parent_id
2. For update tool: use the note's id to find it
3. Always use the exact title as it appears in the user's command for creation

You must always act in a way that is consistent, context-aware, and never lose track of the current note context unless the user explicitly changes it.

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
                json.dump({'notes': [], 'last_note_id': 0}, f, ensure_ascii=False, indent=2)
                
        return file_path

    def _load_notes_and_last_id(self):
        try:
            if os.path.exists(self.notes_file):
                print(f"[DEBUG] Loading notes from: {self.notes_file}")
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    notes = data.get('notes', [])
                    last_note_id = data.get('last_note_id')
                    if last_note_id is None:
                        # Infer from max existing note ID
                        max_id = 0
                        for n in notes:
                            try:
                                max_id = max(max_id, int(n.get('id', 0)))
                            except Exception:
                                pass
                        last_note_id = max_id
                    print(f"[DEBUG] Loaded {len(notes)} notes, last_note_id={last_note_id}")
                    return notes, last_note_id
            else:
                print(f"[DEBUG] Notes file does not exist: {self.notes_file}")
        except Exception as e:
            print(f"[DEBUG] Error loading notes: {e}")
        return [], 0

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
            json.dump({'last_note_id': self.last_note_id, 'notes': self.notes}, f, ensure_ascii=False, indent=2)
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
        try:
            print(f"[DEBUG NLP] process_command called with text: '{text}', language: {language}, conversation_state: {self.conversation_state}")
            print(f"[DEBUG NLP] re module id: {id(re) if 're' in globals() else 'NOT FOUND'}")
            # Add to conversation history
            self.conversation_history.append({'role': 'user', 'text': text, 'language': language})
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            print(f"[DEBUG NLP] Raw text repr: {repr(text)}")
            # Normalize text for robust matching
            normalized_text = unicodedata.normalize('NFKC', text.strip())
            is_hebrew = language == 'he-IL'

            # --- Handle multi-turn state for update/delete/add_sub_note/create after find ---
            if self.conversation_state and self.conversation_state.get('operation') == 'create':
                # Confirmation for create (including sub-notes)
                pending_note = self.conversation_state.get('pending_note')
                pending_title = self.conversation_state.get('pending_title', '')
                pending_action = 'create'
                intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language, 'pending_action': pending_action})
                is_yes = intent_result['intent'] == 'yes'
                is_no = intent_result['intent'] == 'no'
                if is_yes:
                    # Actually create the note (or sub-note)
                    result = self.tools['create'].run(pending_note)
                    self.conversation_state = None
                    self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                    return result
                elif is_no:
                    self.conversation_state = None
                    response = "בסדר, ביטלתי את הפעולה." if is_hebrew else "OK, I've cancelled the action."
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "create_cancel", "response": response, "requires_confirmation": False}
                else:
                    # Ask again
                    response = (
                        f"אנא אשר או בטל: ליצור רשומה חדשה בשם '{pending_title}'?" if is_hebrew
                        else f"Please confirm or cancel: create a new note called '{pending_title}'?"
                    )
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "create_confirm", "response": response, "requires_confirmation": True}
            # --- Sub-note creation intent detection (add_sub_note) ---
            if self.conversation_state and self.conversation_state.get('current_note'):
                current_note = self.conversation_state['current_note']
                # Detect sub-note intent (Hebrew and English)
                subnote_triggers_he = ["תת רשומה", "תת-רשומה", "תוסיף תת רשומה", "הוסף תת רשומה"]
                subnote_triggers_en = ["sub-note", "sub note", "child note", "add sub-note", "add child note"]
                if (is_hebrew and any(trigger in normalized_text for trigger in subnote_triggers_he)) or (not is_hebrew and any(trigger in normalized_text for trigger in subnote_triggers_en)):
                    # Extract sub-note title
                    extract_result = self.tools['extract_sub_note_title'].run({'text': text, 'language': language})
                    title = extract_result.get('title', '').strip()
                    if not title:
                        response = extract_result.get('response', 'Please specify the sub-note title.')
                        self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                        return {"operation": "add_sub_note", "response": response, "requires_confirmation": False}
                    # Check if sub-note already exists under this parent
                    notes = self.notes
                    parent_id = current_note['id']
                    existing_note = next((n for n in notes if n["title"] == title and n.get("parent_id") == parent_id), None)
                    if existing_note:
                        response = (
                            f"רשומת משנה בשם '{title}' כבר קיימת תחת {current_note['title']}." if is_hebrew
                            else f"A sub-note called '{title}' already exists under {current_note['title']}."
                        )
                        self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                        return {"operation": "add_sub_note", "response": response, "requires_confirmation": False}
                    # Prompt for confirmation before creating sub-note
                    response = (
                        f"האם להוסיף תת-רשומה בשם '{title}' תחת '{current_note['title']}'?" if is_hebrew
                        else f"Do you want me to add a sub-note called '{title}' under '{current_note['title']}'?"
                    )
                    self.conversation_state = {
                        'operation': 'create',
                        'pending_note': {
                            'title': title,
                            'parent_id': parent_id,
                            'nlp_service': self,
                            'original_text': text,
                            'requires_confirmation': True
                        },
                        'confirm_action': 'create',
                        'pending_title': title
                    }
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "add_sub_note_confirm", "response": response, "requires_confirmation": True}
            # Hebrew create intent detection
            create_triggers_he = [
                "צור", "הוסף", "חדש", "כתוב", "רשום", "זכור",
                "תיצור", "תיצרי", "תיצרו"
            ]
            if is_hebrew and any(trigger in normalized_text for trigger in create_triggers_he):
                # Use regex to remove trigger + optional 'רשומה חדשה' at the start
                pattern = r'^(?:' + '|'.join(create_triggers_he) + r')\s*(?:רשומה)?\s*(?:חדשה)?\s*(.*)'
                match = re.match(pattern, normalized_text)
                title = match.group(1).strip() if match and match.group(1) else ''
                if not title:
                    title = "ללא שם"  # fallback: Untitled
                # Check if note exists
                notes = self.notes
                existing_note = next((n for n in notes if n["title"] == title), None)
                if existing_note:
                    response = (
                        f"רשומה בשם '{title}' כבר קיימת." if is_hebrew
                        else f"A note with the name '{title}' already exists."
                    )
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "create", "response": response, "requires_confirmation": False}
                # Prompt for confirmation before creating
                response = (
                    f"האם ליצור רשומה חדשה בשם '{title}'?" if is_hebrew
                    else f"Do you want me to create a new note called '{title}'?"
                )
                self.conversation_state = {
                    'operation': 'create',
                    'pending_note': {
                        'title': title,
                        'nlp_service': self,
                        'original_text': text,
                        'requires_confirmation': True
                    },
                    'confirm_action': 'create',
                    'pending_title': title
                }
                self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                return {"operation": "create_confirm", "response": response, "requires_confirmation": True}
            # --- Handle multi-turn state for update/delete/add_sub_note after find ---
            if self.conversation_state and self.conversation_state.get('current_note'):
                print(f"[DEBUG CONTEXT] Using current_note from context: {self.conversation_state['current_note']}")
                current_note = self.conversation_state['current_note']
                is_hebrew = language == 'he-IL'
                # Detect update intent directly after generic prompt
                update_triggers_he = [
                    "עדכן", "שנה", "ערוך", "הוסף ל", "לעדכן", "לעדכן תוכן", "לעדכן רשומה", "לעדכן את הרשומה", "לעדכן את התוכן"
                ]
                update_triggers_en = [
                    "update", "change", "modify", "edit", "add to", "append"
                ]
                update_intent = (
                    (is_hebrew and any(trigger in normalized_text for trigger in update_triggers_he)) or
                    (not is_hebrew and any(trigger in normalized_text for trigger in update_triggers_en))
                )
                if update_intent:
                    # Prompt for new content
                    response = (
                        "מה תרצה לעדכן? אנא אמור את התוכן החדש לרשומה." if is_hebrew
                        else "What would you like to update? Please say the new content for the note."
                    )
                    self.conversation_state = {
                        'operation': 'update_pending_content',
                        'pending_note': {
                            'target_id': current_note['id'],
                            'nlp_service': self
                        },
                        'current_note': current_note
                    }
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "update_ask_content", "response": response, "requires_confirmation": False}
                # Detect delete intent directly after generic prompt
                delete_phrases = [
                    "מחק", "תמחק", "תמחוק", "למחוק", "מחק רשומה", "תמחק רשומה", "תמחוק רשומה",
                    "delete", "remove", "erase", "delete note", "remove note", "erase note"
                ]
                # Use regex for Hebrew variants
                delete_intent = any(phrase in normalized_text for phrase in delete_phrases) or (
                    is_hebrew and re.search(r"\b(מחק|תמחק|תמחוק|למחוק)\b", normalized_text)
                )
                if delete_intent:
                    found_note = current_note
                    self.conversation_state = {
                        'operation': 'delete',
                        'pending_note': {
                            'target_id': found_note['id'],
                            'requires_confirmation': True
                        },
                        'confirm_action': 'delete',
                        'found_note': found_note,
                        'current_note': found_note
                    }
                    response = (
                        f"האם למחוק את הרשומה {found_note['title']}?" if is_hebrew
                        else f"Delete the note {found_note['title']}?"
                    )
                    print(f"[DEBUG DELETE] Returning delete confirmation: {response}")
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {'response': response, 'requires_confirmation': True}
            # --- Existing confirmation state for update/delete ---
            if self.conversation_state and self.conversation_state.get('operation') == 'update':
                print(f"[DEBUG NLP] In update confirmation state: {self.conversation_state}")
                is_hebrew = language == 'he-IL'
                pending_action = 'update'
                intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language, 'pending_action': pending_action})
                print(f"[DEBUG NLP] ConfirmationIntentTool result: {intent_result}")
                print(f"[DEBUG NLP] Operation: update")
                print(f"[DEBUG NLP] Pending note: {self.conversation_state.get('pending_note')}")
                is_yes = intent_result['intent'] == 'yes'
                is_no = intent_result['intent'] == 'no'
                if is_yes:
                    print("[DEBUG NLP] User confirmed update.")
                    pending_note = self.conversation_state.get("pending_note")
                    pending_note["requires_confirmation"] = False
                    if 'nlp_service' not in pending_note:
                        pending_note['nlp_service'] = self
                    tool = self.tools.get('update')
                    if tool:
                        result = tool.run(pending_note)
                        result["notes_updated"] = True
                    else:
                        result = {"response": "Error: Update tool not found."}
                    self.conversation_state = None
                    print(f"[DEBUG NLP] Returning result after update confirmation: {result}")
                    self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                    return result
                elif is_no:
                    print("[DEBUG NLP] User denied update.")
                    self.conversation_state = None
                    result = {
                        "response": "בסדר, ביטלתי את הפעולה." if is_hebrew else "OK, I've cancelled the action."
                    }
                    self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                    return result
                else:
                    # Ambiguous: prompt again for confirmation
                    current_note = self.conversation_state.get('current_note')
                    updates = self.conversation_state.get('pending_note', {}).get('updates', '')
                    response = (
                        f"אנא אשר או בטל: לעדכן את הרשומה '{current_note['title']}' עם התוכן הבא?\n{updates}" if is_hebrew
                        else f"Please confirm or cancel: update the note '{current_note['title']}' with the following content?\n{updates}"
                    )
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "update_confirm", "response": response, "requires_confirmation": True}
            # --- Confirmation state for delete ---
            if self.conversation_state and self.conversation_state.get('operation') == 'delete':
                print(f"[DEBUG NLP] In delete confirmation state: {self.conversation_state}")
                is_hebrew = language == 'he-IL'
                pending_action = 'delete'
                intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language, 'pending_action': pending_action})
                print(f"[DEBUG NLP] ConfirmationIntentTool result: {intent_result}")
                print(f"[DEBUG NLP] Operation: delete")
                print(f"[DEBUG NLP] Pending note: {self.conversation_state.get('pending_note')}")
                is_yes = intent_result['intent'] == 'yes'
                is_no = intent_result['intent'] == 'no'
                if is_yes:
                    print("[DEBUG NLP] User confirmed delete.")
                    pending_note = self.conversation_state.get("pending_note")
                    pending_note["requires_confirmation"] = False
                    if 'nlp_service' not in pending_note:
                        pending_note['nlp_service'] = self
                    tool = self.tools.get('delete')
                    if tool:
                        result = tool.run(pending_note)
                    else:
                        result = {"response": "Error: Delete tool not found.", "operation": "delete"}
                    self.conversation_state = None
                    print(f"[DEBUG NLP] Returning result after delete confirmation: {result}")
                    self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                    return result
                elif is_no:
                    print("[DEBUG NLP] User denied delete.")
                    self.conversation_state = None
                    result = {
                        "response": "בסדר, ביטלתי את הפעולה." if is_hebrew else "OK, I've cancelled the action.",
                        "operation": "delete_cancel"
                    }
                    self.conversation_history.append({'role': 'agent', 'text': result['response'], 'language': language})
                    return result
                else:
                    # Ambiguous: prompt again for confirmation
                    current_note = self.conversation_state.get('current_note')
                    response = (
                        f"אנא אשר או בטל: למחוק את הרשומה '{current_note['title']}'?" if is_hebrew
                        else f"Please confirm or cancel: delete the note '{current_note['title']}'?"
                    )
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "delete_confirm", "response": response, "requires_confirmation": True}
            # --- Multi-turn: handle pending update content ---
            if self.conversation_state and self.conversation_state.get('operation') == 'update_pending_content':
                # The user's message is the new content for the update
                current_note = self.conversation_state.get('current_note')
                pending_note = self.conversation_state.get('pending_note', {})
                # Check if the user input is a confirmation/denial (should not be treated as content)
                intent_result = self.tools['confirmation_intent'].run({'text': text, 'language': language, 'pending_action': 'update'})
                if intent_result['intent'] in ('yes', 'no'):
                    # User said 'yes' or 'no' instead of providing content
                    is_hebrew = language == 'he-IL'
                    response = (
                        "אנא אמור את התוכן החדש לעדכון הרשומה." if is_hebrew
                        else "Please provide the new content to update the note."
                    )
                    self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                    return {"operation": "update_ask_content", "response": response, "requires_confirmation": False}
                # Otherwise, treat as new content
                pending_note['updates'] = text.strip()
                # Prompt for confirmation
                is_hebrew = language == 'he-IL'
                response = (
                    f"האם לעדכן את הרשומה '{current_note['title']}' עם התוכן הבא?\n{text.strip()}" if is_hebrew
                    else f"Update the note '{current_note['title']}' with the following content?\n{text.strip()}"
                )
                self.conversation_state = {
                    'operation': 'update',
                    'pending_note': pending_note,
                    'confirm_action': 'update',
                    'current_note': current_note
                }
                self.conversation_history.append({'role': 'agent', 'text': response, 'language': language})
                return {"operation": "update_confirm", "response": response, "requires_confirmation": True}
            # --- Find command: update context if single note found ---
            response = self.tools['find'].run({'query': text, 'nlp_service': self})
            matches = response.get('matches', [])
            if len(matches) == 1:
                print(f"[DEBUG CONTEXT] Switching context to note: {matches[0]}")
                self.conversation_state = {'current_note': matches[0]}
                response_text = (
                    "נמצאה רשומה אחת. האם תרצה לעדכן, למחוק או להוסיף תת-רשומה?"
                    if language == 'he-IL'
                    else "Found 1 note. Would you like to update, delete, or add a sub-note?"
                )
                return {
                    "response": response_text,
                    "matches": matches,
                    "requires_confirmation": True
                }
            return response
        except Exception as e:
            print(f"[AGENT ERROR] {e}\n{traceback.format_exc()}")
            # Fallback message to user
            is_hebrew = language == 'he-IL'
            fallback_msg = (
                "מצטער, לא הצלחתי להבין את הבקשה שלך. תוכל לנסח שוב או להבהיר מה תרצה לעשות?"
                if is_hebrew else
                "Sorry, I ran into a problem understanding your request. Could you please clarify what you want to do?"
            )
            # Try to send message to user if possible
            try:
                if hasattr(self, 'app_instance') and hasattr(self.app_instance, 'main_screen'):
                    self.app_instance.main_screen.add_chat_message('agent', fallback_msg)
            except Exception as e2:
                print(f"[AGENT ERROR] Could not send fallback message: {e2}")
            # Reset conversation state
            self.conversation_state = None
            return {"response": fallback_msg, "error": str(e)}

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

WELCOME_MESSAGE_EN = (
    "Welcome to Note Speaker!\n"
    "You can control the app with your voice. Here are some examples:\n\n"
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
    "Mark as done: 'mark note as done'\n"
    "The app will always ask for confirmation before creating or deleting notes.\n\n"
    "Say 'yes' or 'no' to confirm or cancel actions.\n\n"
    "You can change this setting in the Settings window."
)
WELCOME_MESSAGE_HE = (
    "ברוכים הבאים ל-Note Speaker!\n"
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
    "סימון כהושלמה: 'סמן רשומה כהושלמה'\n"
    "האפליקציה תמיד תבקש ממך אישור לפני יצירה או מחיקה של רשומות.\n\n"
    "אמור 'כן' או 'לא' כדי לאשר או לבטל פעולות.\n\n"
    "ניתן לשנות הגדרה זו בחלון ההגדרות."
) 