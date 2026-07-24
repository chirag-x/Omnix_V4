import speech_recognition as sr
import threading


class SpeechRecognizer:

    def __init__(self, calibrate=True):

        self.recognizer = sr.Recognizer()

        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 2.0
        self.recognizer.phrase_threshold = 0.5

        if not hasattr(SpeechRecognizer, "_shared_mic"):
            SpeechRecognizer._shared_mic = sr.Microphone()

        if not hasattr(SpeechRecognizer, "_mic_lock"):
            SpeechRecognizer._mic_lock = threading.RLock()

        self.microphone = SpeechRecognizer._shared_mic

        if calibrate:
            try:
                with SpeechRecognizer._mic_lock:
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(
                            source, duration=1)
            except Exception:
                pass

    def listen_command(self):

        try:

            with SpeechRecognizer._mic_lock:
                with self.microphone as source:

                    print("[SpeechRecognizer] Listening for command...")

                    audio = self.recognizer.listen(
                        source,
                        timeout=10,
                        phrase_time_limit=15
                    )

            text = self.recognizer.recognize_google(audio)

            print(f"[SpeechRecognizer] Heard command: {text}")

            if text:
                return text.lower().strip()

        except sr.WaitTimeoutError:
            print("[SpeechRecognizer] Timeout waiting for speech")
            return None

        except Exception as e:
            print(f"[SpeechRecognizer ERROR]: {e}")
            return None
