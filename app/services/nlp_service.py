import google.generativeai as genai
from typing import Dict, List, Optional
import json
import os
import re
from kivy.utils import platform

class NoteTool:
    """Base class for note management tools"""
    def __init__(self, notes: List[Dict]):
        self.notes = notes

    def run(self, params: Dict) -> Dict:
        raise NotImplementedError

class CreateNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        print(f"[DEBUG] CreateNoteTool running with params: {params}")
        title = params.get("title")
        description = params.get("description")
        parent_id = params.get("parent_id")
        
        # Fallback: if title is None or empty, use the user's original text
        if not title:
            title = params.get("original_text", "Untitled")
        if not description:
            description = ""
            
        # Check if we're dealing with Hebrew text
        is_hebrew = title and any(c > 'z' for c in title)
        
        # If parent_id is specified, try to find parent by ID or title
        if parent_id:
            parent = next((n for n in self.notes if n["id"] == parent_id), None)
            if not parent:
                parent = next((n for n in self.notes if n["title"] == parent_id), None)
            if not parent:
                response = (
                    f"רשומת האב לא נמצאה" if is_hebrew
                    else f"Parent note not found"
                )
                return {
                    "operation": "error",
                    "response": response
                }
            # Use the actual parent ID
            parent_id = parent["id"]
        
        # Check if a note with the same title already exists
        existing_note = next((n for n in self.notes if n["title"] == title), None)
        if existing_note:
            response = (
                f"רשומה בשם '{title}' כבר קיימת. האם ברצונך לעדכן אותה?" if is_hebrew
                else f"A note with the name '{title}' already exists. Do you want to override it?"
            )
            return {
                "operation": "override_confirm",
                "response": response,
                "requires_confirmation": True,
                "pending_note": {
                    "title": title,
                    "description": description,
                    "parent_id": parent_id,
                    "override": True
                }
            }
            
        # Create the note if no confirmation required
        if not params.get("requires_confirmation", True):
            new_note = {
                "id": str(len(self.notes) + 1),
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
            self.notes.append(new_note)
            
            # Update parent's children list if parent_id is specified
            if parent_id:
                parent = next(n for n in self.notes if n["id"] == parent_id)
                parent["children"].append(new_note["id"])
            
            response = (
                f'נוצרה רשומה: {title}' if is_hebrew
                else f'Created note: {title}'
            )
            return {
                "operation": "create",
                "response": response,
                "requires_confirmation": False
            }
            
        # Otherwise, ask for confirmation
        response = (
            f"האם ליצור רשומה בשם {title}?" if is_hebrew
            else f"Do you want me to create a note called {title}?"
        )
        return {
            "operation": "create",
            "response": response,
            "requires_confirmation": True,
            "pending_note": {
                "title": title,
                "description": description,
                "parent_id": parent_id
            }
        }

class UpdateNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        print(f"[DEBUG] UpdateNoteTool running with params: {params}")
        target_id = params.get("target_id")
        updates = params.get("updates", "")
        
        # Check if we're dealing with Hebrew text
        is_hebrew = target_id and any(c > 'z' for c in target_id)
        
        # First try to find note by ID, then by title if ID not found
        note = next((n for n in self.notes if n["id"] == target_id), None)
        if not note:
            note = next((n for n in self.notes if n["title"] == target_id), None)
            
        if note:
            # If updates is a string, append it to description
            if isinstance(updates, str):
                current_desc = note.get("description", "")
                if current_desc:
                    note["description"] = current_desc + "\n" + updates
                else:
                    note["description"] = updates
            # If updates is a dict, update the note fields
            elif isinstance(updates, dict):
                note.update(updates)
                
            print(f"[DEBUG] Updated note: {note}")
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
        print(f"[DEBUG] DeleteNoteTool running with params: {params}")
        target_id = params.get("target_id")
        note = next((n for n in self.notes if n["id"] == target_id), None)
        if note:
            self.notes.remove(note)
            print(f"[DEBUG] Deleted note: {note}")
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
        print(f"[DEBUG] FindNoteTool running with params: {params}")
        query = params.get("query", "")
        
        # Check if query is in Hebrew
        is_hebrew = query and any(c > 'z' for c in query)
        
        # For Hebrew text, do exact match. For non-Hebrew, do case-insensitive match
        matches = []
        for note in self.notes:
            title = note.get("title") or ""
            desc = note.get("description") or ""
            
            if is_hebrew:
                # For Hebrew, do exact match
                if query in title or query in desc:
                    matches.append(note)
            else:
                # For non-Hebrew, do case-insensitive match
                if query.lower() in title.lower() or query.lower() in desc.lower():
                    matches.append(note)
        
        print(f"[DEBUG] Found {len(matches)} matches: {matches}")
        
        response = f"נמצאו {len(matches)} רשומות" if is_hebrew else f"Found {len(matches)} notes"
        
        return {
            "operation": "find",
            "response": response,
            "matches": matches
        }

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
        
        # Initialize tools with notes
        self.tools = {
            "create": CreateNoteTool(self.notes),
            "update": UpdateNoteTool(self.notes),
            "delete": DeleteNoteTool(self.notes),
            "find": FindNoteTool(self.notes)
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
        try:
            print(f"[DEBUG] Saving {len(self.notes)} notes to: {self.notes_file}")
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump({'notes': self.notes}, f, ensure_ascii=False, indent=2)
            print("[DEBUG] Notes saved successfully")
        except Exception as e:
            print(f"[DEBUG] Error saving notes: {e}")

    def process_command(self, text: str, language: str = 'en') -> Dict:
        """Process a natural language command"""
        if not self.model:
            return {
                "operation": "error",
                "response": "Gemini API key not configured. Please set the GEMINI_API_KEY environment variable."
            }
            
        try:
            # Handle confirmation responses
            if self.conversation_state:
                print(f"[DEBUG] Current conversation state: {self.conversation_state}")
                # Check for confirmation in both English and Hebrew
                confirmation_words = {'yes', 'yeah', 'sure', 'ok', 'okay', 'כן', 'בסדר', 'אישור', 'אוקיי', 'כ'}
                rejection_words = {'no', 'nope', 'לא', 'לו'}
                
                # Clean up the text for comparison
                cleaned_text = text.lower().strip().replace('.', '').replace('!', '')
                
                # Check if this is a confirmation
                is_confirmation = any(word in cleaned_text for word in confirmation_words)
                is_rejection = any(word in cleaned_text for word in rejection_words)
                
                print(f"[DEBUG] Cleaned text: '{cleaned_text}', is_confirmation: {is_confirmation}, is_rejection: {is_rejection}")
                
                if is_confirmation or is_rejection:
                    print(f"[DEBUG] Processing {'confirmation' if is_confirmation else 'rejection'}")
                    
                    if is_rejection:
                        self.conversation_state = None
                        return {
                            "operation": "cancelled",
                            "response": "בוטל." if language == 'he-IL' else "Cancelled."
                        }
                    
                    operation = self.conversation_state.get('operation')
                    pending_note = self.conversation_state.get('pending_note')
                    
                    print(f"[DEBUG] Operation: {operation}, Pending note: {pending_note}")
                    
                    if operation == 'create' and pending_note:
                        # Create the new note
                        new_note = {
                            "id": str(len(self.notes) + 1),
                            "title": pending_note["title"],
                            "description": pending_note.get("description", ""),
                            "parent_id": pending_note.get("parent_id"),
                            "children": [],
                            "done": False,
                            "done_date": None,
                            "relations": {},
                            "links": [],
                            "tags": []
                        }
                        print(f"[DEBUG] Creating new note: {new_note}")
                        self.notes.append(new_note)
                        
                        # Update parent's children list if parent_id is specified
                        if pending_note.get("parent_id"):
                            parent = next((n for n in self.notes if n["id"] == pending_note["parent_id"]), None)
                            if parent:
                                parent["children"].append(new_note["id"])
                                print(f"[DEBUG] Updated parent note {parent['title']} with new child")
                        
                        self._save_notes()
                        self.conversation_state = None
                        
                        response = (
                            f'נוצרה רשומה: {pending_note["title"]}' if language == 'he-IL'
                            else f'Created note: {pending_note["title"]}'
                        )
                        return {
                            "operation": "create",
                            "response": response,
                            "requires_confirmation": False
                        }
                    
                    print("[DEBUG] No valid operation or pending note found in conversation state")
                    self.conversation_state = None
                    return {
                        "operation": "error",
                        "response": "אין רשומה ממתינה לאישור." if language == 'he-IL' else "No pending note to confirm."
                    }
                
                # If not a confirmation or rejection, clear the state and process as new command
                print("[DEBUG] Not a confirmation/rejection response, clearing state")
                self.conversation_state = None
            
            # Process command with Gemini
            prompt = f"{self.tool_selection_prompt}\nUser command: {text}"
            response = self.model.generate_content(prompt)
            print(f"[DEBUG] Gemini raw response: {response.text}")
            
            # Clean up response text - remove markdown code blocks
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("\n", 1)[0]
            if response_text.startswith("json\n"):
                response_text = response_text[5:]
            response_text = response_text.strip()
            
            # Parse the response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"[DEBUG] Error parsing Gemini response: {response_text}")
                print(f"[DEBUG] JSON parse error: {e}")
                return {
                    "operation": "error",
                    "response": "Sorry, I couldn't understand how to process that command."
                }
                
            # Get the selected tool
            tool_name = result.get("tool", "unknown")
            if tool_name == "unknown":
                return {
                    "operation": "error",
                    "response": "I'm not sure how to help with that. Could you rephrase your request?"
                }
                
            # Run the tool
            tool = self.tools.get(tool_name)
            if not tool:
                return {
                    "operation": "error",
                    "response": f"Tool '{tool_name}' not found."
                }
                
            # Execute the tool with parameters
            tool_result = tool.run(result.get("params", {}))
            
            # If confirmation is required, store the state
            if tool_result.get("requires_confirmation", False):
                print(f"[DEBUG] Storing conversation state: {tool_result}")
                self.conversation_state = {
                    'operation': tool_result.get('operation'),
                    'pending_note': tool_result.get('pending_note')
                }
            
            # Save notes if the operation was successful and doesn't require confirmation
            if not tool_result.get("requires_confirmation", False) and tool_result.get("operation") not in ["error", "find"]:
                self._save_notes()
                
            return tool_result
            
        except Exception as e:
            print(f"[DEBUG] Error processing command: {e}")
            return {
                "operation": "error",
                "response": f"Error processing command: {e}"
            }

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