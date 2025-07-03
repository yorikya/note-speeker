import speech_recognition as sr
import threading
import time
from kivy.clock import Clock
from gtts import gTTS
import os
import subprocess


class SpeechService:
    """Speech recognition service with multi-language support"""
    
    # Supported languages dictionary (name -> code)
    SUPPORTED_LANGUAGES = {
        'English (US)': 'en-US',
        'Hebrew': 'he-IL',
    }
    
    # Languages dictionary (code -> name) for modern UI
    LANGUAGES = {code: name for name, code in SUPPORTED_LANGUAGES.items()}

    def __init__(self, config_service=None):
        self.config_service = config_service
        self.recognizer = sr.Recognizer()
        self.current_language = (config_service.get('speech_language', 'en-US') if config_service else "en-US")
        self.is_listening = False
        self.listen_thread = None
        self.stop_listening_flag = False
        # Configure recognizer for better performance
        self.energy_threshold = config_service.get_voice_energy_threshold() if config_service and hasattr(config_service, 'get_voice_energy_threshold') else 100
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8

    def set_language(self, language_code):
        """Set the current language for speech recognition"""
        if language_code in self.SUPPORTED_LANGUAGES.values():
            self.current_language = language_code
            # Save to config if available
            if self.config_service:
                self.config_service.set('speech_language', language_code)
                self.config_service.save_config()
            print(f"Language set to: {language_code}")
            return True
        return False

    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.SUPPORTED_LANGUAGES
    
    def start_listening(self, on_result=None, on_error=None, on_auto_stop=None, silence_timeout=5, recording_timeout=600):
        """Start continuous listening in a separate thread with auto-stop features"""
        if self.is_listening:
            return False
            
        self.is_listening = True
        self.stop_listening_flag = False
        
        def listen_continuously():
            """Continuous listening function with timeout management"""
            start_time = time.time()
            last_speech_time = start_time
            print("[DEBUG SR] Entered listen_continuously thread.")
            try:
                with sr.Microphone() as source:
                    time.sleep(0.3)  # Wait 300ms before starting to listen
                    print(f"Starting continuous listening in {self.current_language}...")
                    print(f"Auto-stop after {silence_timeout}s silence or {recording_timeout}s total")
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    while not self.stop_listening_flag:
                        current_time = time.time()
                        # Print current energy threshold for debugging
                        print(f"[DEBUG SR] Current energy_threshold: {self.recognizer.energy_threshold}")
                        # Check for total recording timeout (10 minutes default)
                        if current_time - start_time > recording_timeout:
                            print(f"Auto-stopping: Recording timeout ({recording_timeout}s) reached")
                            if on_auto_stop:
                                Clock.schedule_once(lambda dt: on_auto_stop("Recording timeout reached"), 0)
                            break
                        # Check for silence timeout
                        if current_time - last_speech_time > silence_timeout:
                            print(f"Auto-stopping: Silence timeout ({silence_timeout}s) reached")
                            if on_auto_stop:
                                Clock.schedule_once(lambda dt: on_auto_stop("Silence timeout reached"), 0)
                            break
                        try:
                            # Listen for audio with a shorter timeout for responsiveness
                            print("[DEBUG SR] Listening for audio...")
                            audio = self.recognizer.listen(
                                source, 
                                timeout=1,  # Check every second for timeouts
                                phrase_time_limit=15
                            )
                            print("[DEBUG SR] Audio received, recognizing...")
                            print(f"[DEBUG SR] Audio duration: {getattr(audio, 'duration_seconds', 'N/A')} seconds")
                            if self.stop_listening_flag:
                                break
                            # Recognize speech
                            text = self.recognizer.recognize_google(
                                audio, 
                                language=self.current_language
                            )
                            print(f"[DEBUG SR] Recognized text: {text}")
                            if text.strip():
                                # Update last speech time when we get actual speech
                                last_speech_time = time.time()
                                if on_result:
                                    print("[DEBUG SR] Calling on_result callback...")
                                    Clock.schedule_once(lambda dt: on_result(text.strip()), 0)
                        except sr.WaitTimeoutError:
                            print("[DEBUG SR] WaitTimeoutError: No speech detected in timeout window.")
                            continue
                        except sr.UnknownValueError:
                            print("[DEBUG SR] UnknownValueError: Could not understand audio.")
                            last_speech_time = time.time()
                            continue
                        except sr.RequestError as e:
                            error_msg = f"Recognition service error: {e}"
                            print(f"[DEBUG SR] RequestError: {error_msg}")
                            if on_error:
                                Clock.schedule_once(lambda dt: on_error(error_msg), 0)
                            break
                        except Exception as e:
                            error_msg = f"Unexpected error: {e}"
                            print(f"[DEBUG SR] Exception: {error_msg}")
                            if on_error:
                                Clock.schedule_once(lambda dt: on_error(error_msg), 0)
                            break
            except Exception as e:
                error_msg = f"Microphone error: {e}"
                print(f"[DEBUG SR] Outer Exception: {error_msg}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(error_msg), 0)
            finally:
                self.is_listening = False
                print("Stopped listening")
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=listen_continuously, daemon=True)
        self.listen_thread.start()
        return True
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.stop_listening_flag = True
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)

    def speak_text(self, text):
        """Convert text to speech and play it based on the current language setting."""
        print(f"[DEBUG TTS] speak_text called with text: '{text}'")
        
        lang_code_map = {
            'he-IL': 'iw',  # Hebrew
            'en-US': 'en',  # English
        }
        
        gtts_lang = lang_code_map.get(self.current_language)
        
        if not gtts_lang:
            print(f"[DEBUG TTS] TTS not supported for language: {self.current_language}")
            return

        try:
            print("[DEBUG TTS] Generating speech with gTTS...")
            # gTTS uses 'iw' for Hebrew
            tts = gTTS(text=text, lang=gtts_lang)
            # Use a temporary file to store the speech
            temp_file = "temp_speech.mp3"
            tts.save(temp_file)
            print(f"[DEBUG TTS] Saved speech to {temp_file}")
            
            # Use afplay on macOS to play the audio with a timeout.
            try:
                print("[DEBUG TTS] Playing audio with subprocess...")
                subprocess.run(["afplay", temp_file], timeout=10, check=True, capture_output=True)
                print("[DEBUG TTS] Audio playback finished.")
            except subprocess.TimeoutExpired:
                print(f"[DEBUG TTS] TTS playback timed out for file: {temp_file}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"[DEBUG TTS] Error playing TTS file: {e}")
            
            # Clean up the temporary file
            if os.path.exists(temp_file):
                print(f"[DEBUG TTS] Removing temporary file: {temp_file}")
                os.remove(temp_file)
            
        except Exception as e:
            print(f"[DEBUG TTS] General error in TTS: {e}")

    def listen(self, language=None, silence_timeout=5):
        """Single-shot speech recognition function (legacy compatibility)"""
        # Use provided language or fallback to current language
        lang = language or self.current_language
        
        try:
            with sr.Microphone() as source:
                print(f"Listening in {lang}... (will stop after {silence_timeout} seconds of silence)")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=silence_timeout, phrase_time_limit=None)
                text = self.recognizer.recognize_google(audio, language=lang)
                print(f"You said: {text}")
                return text
        except sr.WaitTimeoutError:
            print("Stopped listening due to silence.")
            return ""
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""
        except Exception as e:
            print(f"Unexpected error: {e}")
            return ""

    def set_energy_threshold(self, value):
        self.energy_threshold = value
        self.recognizer.energy_threshold = value
        if self.config_service and hasattr(self.config_service, 'set_voice_energy_threshold'):
            self.config_service.set_voice_energy_threshold(value)

    def get_energy_level(self):
        return self.recognizer.energy_threshold 