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
        # Fallback: if title is None or empty, use the user's original text (passed as 'original_text' in params)
        if not title:
            title = params.get("original_text", "Untitled")
        if not description:
            description = ""
        # Check if a note with the same title already exists
        existing_note = next((n for n in self.notes if n["title"] == title), None)
        if existing_note:
            return {
                "operation": "override_confirm",
                "response": f"A note with the name '{title}' already exists. Do you want to override it?",
                "requires_confirmation": True,
                "pending_note": {
                    "title": title,
                    "description": description,
                    "parent_id": params.get("parent_id"),
                    "override": True
                }
            }
        # Do not create the note yet, just return the pending note for confirmation
        return {
            "operation": "create",
            "response": f"Do you want me to create a note called {title}?",
            "requires_confirmation": True,
            "pending_note": {
                "title": title,
                "description": description,
                "parent_id": params.get("parent_id")
            }
        }

class UpdateNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        print(f"[DEBUG] UpdateNoteTool running with params: {params}")
        target_id = params.get("target_id")
        updates = params.get("updates", {})
        
        note = next((n for n in self.notes if n["id"] == target_id), None)
        if note:
            note.update(updates)
            print(f"[DEBUG] Updated note: {note}")
            return {
                "operation": "update",
                "response": f"Updated note: {note['title']}"
            }
        print(f"[DEBUG] Note not found with id: {target_id}")
        return {
            "operation": "error",
            "response": "Note not found"
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
            "response": "Note not found"
        }

class FindNoteTool(NoteTool):
    def run(self, params: Dict) -> Dict:
        print(f"[DEBUG] FindNoteTool running with params: {params}")
        query = params.get("query", "")
        matches = [
            note for note in self.notes 
            if query.lower() in (note.get("title") or "").lower() or 
               query.lower() in (note.get("description") or "").lower()
        ]
        print(f"[DEBUG] Found {len(matches)} matches: {matches}")
        return {
            "operation": "find",
            "response": f"Found {len(matches)} notes",
            "matches": matches
        }

class NLPService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
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
   - Trigger phrases: "create", "new", "add", "make", "write", "note down", "remember"
   - Example: "I need to remember to buy milk" -> create a note about buying milk
   - Example: "Let me write down my meeting notes" -> create a note with meeting notes

2. update - Update an existing note
   - Trigger phrases: "update", "change", "modify", "edit", "add to", "append"
   - Example: "Add 'bring documents' to my meeting notes" -> update meeting notes
   - Example: "Change the title of my shopping list" -> update note title

3. delete - Delete a note
   - Trigger phrases: "delete", "remove", "erase", "clear", "forget"
   - Example: "I don't need that shopping list anymore" -> delete shopping list
   - Example: "Remove my old meeting notes" -> delete meeting notes

4. find - Search for notes
   - Trigger phrases: "find", "search", "look for", "where is", "show me"
   - Example: "Where did I write about the meeting?" -> find notes about meeting
   - Example: "Show me my shopping lists" -> find shopping lists

For each tool, extract these parameters:
- create: title, description, parent_id (optional)
- update: target_id, updates (what to change)
- delete: target_id
- find: query

If the command is not clear or doesn't match any tool's purpose, return "unknown" as the tool.

Return a JSON with:
{
    "tool": "tool_name",
    "params": {tool specific parameters},
    "response": "natural language response",
    "requires_confirmation": true/false
}
"""

    def _get_notes_file_path(self) -> str:
        if platform == 'android':
            from android.storage import primary_external_storage_path
            notes_dir = primary_external_storage_path()
        else:
            notes_dir = os.path.expanduser('~')
        notes_path = os.path.join(notes_dir, '.note_speaker')
        print(f"[DEBUG] Notes directory: {notes_path}")
        if not os.path.exists(notes_path):
            os.makedirs(notes_path)
            print(f"[DEBUG] Created notes directory: {notes_path}")
        file_path = os.path.join(notes_path, 'notes.json')
        print(f"[DEBUG] Notes file path: {file_path}")
        return file_path

    def _load_notes(self) -> List[Dict]:
        try:
            if os.path.exists(self.notes_file):
                print(f"[DEBUG] Loading notes from: {self.notes_file}")
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    notes = json.load(f)
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
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
            print("[DEBUG] Notes saved successfully")
        except Exception as e:
            print(f"[DEBUG] Error saving notes: {e}")

    def process_command(self, text: str, language: str = 'en') -> Dict:
        print(f"[DEBUG] Processing command: {text} (language: {language})")
        # Handle confirmation responses
        if self.conversation_state and text.lower() in ['yes', 'yeah', 'sure', 'ok', 'okay', 'כן', 'בסדר']:
            print("[DEBUG] Processing confirmation")
            pending = self.conversation_state.get("pending_note")
            if pending:
                # If override is requested, update the existing note
                if pending.get("override"):
                    for n in self.notes:
                        if n["title"] == pending["title"]:
                            n["description"] = pending["description"]
                            n["parent_id"] = pending.get("parent_id")
                            break
                    self._save_notes()
                    self.conversation_state = None
                    return {
                        "operation": "override",
                        "response": f"Note '{pending['title']}' was overridden."
                    }
                # Actually create the note now
                new_note = {
                    "id": str(len(self.notes) + 1),
                    "title": pending["title"],
                    "description": pending["description"],
                    "parent_id": pending.get("parent_id"),
                    "children": [],
                    "done": False,
                    "done_date": None,
                    "relations": {},
                    "links": [],
                    "tags": []
                }
                self.notes.append(new_note)
                self._save_notes()
                self.conversation_state = None
                return {
                    "operation": "create",
                    "response": f"Created note: {pending['title']}"
                }
            self.conversation_state = None
            return {
                "operation": "error",
                "response": "No pending note to confirm."
            }
        prompt = f"""
{self.tool_selection_prompt}
Current notes structure:
{json.dumps(self.notes, indent=2)}
User command: {text}
Language: {language}

Respond ONLY with a valid JSON object, no explanation, no markdown, no text before or after.
"""
        try:
            response = self.model.generate_content(prompt)
            print("[DEBUG] Gemini raw response:", response.text)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
                raw = re.sub(r"```$", "", raw)
            raw = raw.strip()
            result = json.loads(raw)
            print(f"[DEBUG] Parsed result: {result}")
            if result["tool"] == "unknown":
                print("[DEBUG] Command not understood, returning unknown")
                return {
                    "operation": "unknown",
                    "response": "I didn't understand the command"
                }
            # Route to appropriate tool
            tool = self.tools.get(result["tool"])
            if tool:
                # Always pass the original user text for fallback
                if "params" in result:
                    result["params"]["original_text"] = text
                print(f"[DEBUG] Routing to tool: {result['tool']}")
                tool_result = tool.run(result["params"])
                # If confirmation is required, store the state
                if tool_result.get("requires_confirmation", False):
                    self.conversation_state = tool_result
                    return {
                        "operation": tool_result.get("operation", "confirm"),
                        "response": tool_result["response"]
                    }
                self._save_notes()  # Save after any tool operation
                return tool_result
            else:
                print(f"[DEBUG] Unknown tool requested: {result['tool']}")
                return {
                    "operation": "error",
                    "response": f"Unknown tool: {result['tool']}"
                }
        except Exception as e:
            print(f"[DEBUG] Error processing command: {e}")
            print("[DEBUG] Gemini raw response (error):", getattr(locals().get('response', None), 'text', None))
            return {
                "operation": "error",
                "response": f"Error processing command: {str(e)}"
            } 