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
                from android.storage import primary_external_storage_path
                base_dir = primary_external_storage_path()
            except Exception:
                base_dir = "/sdcard"
            log_dir = os.path.join(base_dir, "note_speaker")
        else:
            log_dir = os.path.join(os.path.expanduser("~"), ".note_speaker")
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, log_filename)

    def _redirect_stdout_stderr(self):
        log_file = open(self.log_file_path, "a", buffering=1, encoding="utf-8")
        sys.stdout = log_file
        sys.stderr = log_file
        print(f"[LOG] Logging started. Log file: {self.log_file_path}")

# Usage: from app.services.log_service import LogService; LogService() 