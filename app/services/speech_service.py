import speech_recognition as sr
import threading
import time
from kivy.clock import Clock


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
        # Get default language from config or use fallback
        self.current_language = (config_service.get('speech_language', 'en-US') 
                               if config_service else "en-US")
        self.is_listening = False
        self.listen_thread = None
        self.stop_listening_flag = False
        
        # Configure recognizer for better performance
        self.recognizer.energy_threshold = 300
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
            
            try:
                with sr.Microphone() as source:
                    print(f"Starting continuous listening in {self.current_language}...")
                    print(f"Auto-stop after {silence_timeout}s silence or {recording_timeout}s total")
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    
                    while not self.stop_listening_flag:
                        current_time = time.time()
                        
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
                            audio = self.recognizer.listen(
                                source, 
                                timeout=1,  # Check every second for timeouts
                                phrase_time_limit=15
                            )
                            
                            if self.stop_listening_flag:
                                break
                                
                            # Recognize speech
                            text = self.recognizer.recognize_google(
                                audio, 
                                language=self.current_language
                            )
                            
                            if text.strip():
                                # Update last speech time when we get actual speech
                                last_speech_time = time.time()
                                if on_result:
                                    Clock.schedule_once(lambda dt: on_result(text.strip()), 0)
                                
                        except sr.WaitTimeoutError:
                            # Timeout is normal, continue listening (but don't reset speech timer)
                            continue
                        except sr.UnknownValueError:
                            # Could not understand audio (but there was audio, so reset timer)
                            last_speech_time = time.time()
                            continue
                        except sr.RequestError as e:
                            error_msg = f"Recognition service error: {e}"
                            if on_error:
                                Clock.schedule_once(lambda dt: on_error(error_msg), 0)
                            break
                        except Exception as e:
                            error_msg = f"Unexpected error: {e}"
                            if on_error:
                                Clock.schedule_once(lambda dt: on_error(error_msg), 0)
                            break
                            
            except Exception as e:
                error_msg = f"Microphone error: {e}"
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