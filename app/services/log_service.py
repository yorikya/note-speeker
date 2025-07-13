import os
import sys
from kivy.utils import platform

class LogService:
    def __init__(self, log_filename="note_speaker.log"):
        self.log_file_path = self._get_log_file_path(log_filename)
        self._redirect_stdout_stderr()

    def _get_log_file_path(self, log_filename):
        if platform == 'android':
            try:
                # Request permissions at runtime
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE
                ])
                # Use app-specific external storage directory
                from android.storage import app_storage_path
                base_dir = app_storage_path()  # /storage/emulated/0/Android/data/com.yorikya.notespeaker/files
            except Exception as e:
                print(f"[LOG] Android storage/permissions error: {e}")
                base_dir = "/sdcard/note_speaker_fallback"
            log_dir = base_dir
        else:
            log_dir = os.path.join(os.path.expanduser("~"), ".note_speaker")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, log_filename)

    def _redirect_stdout_stderr(self):
        try:
            log_file = open(self.log_file_path, "a", buffering=1, encoding="utf-8")
            sys.stdout = log_file
            sys.stderr = log_file
            print(f"[LOG] Logging started. Log file: {self.log_file_path}")
        except Exception as e:
            # Print error to logcat and continue without crashing
            import traceback
            print(f"[LOG ERROR] Could not open log file: {e}\n{traceback.format_exc()}")

    def write_log_entry(self, message):
        """
        Write a log entry directly to the log file (useful for explicit logging).
        If writing fails (e.g., due to permissions), print the error but do not crash.
        """
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(message + '\n')
        except Exception as e:
            import traceback
            print(f"[LOG ERROR] Could not write log entry: {e}\n{traceback.format_exc()}")

# Usage: from app.services.log_service import LogService; LogService() 