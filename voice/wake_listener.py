import speech_recognition as sr
import time
import threading
from voice.speech_recognizer import SpeechRecognizer


class WakeListener:

    def __init__(self, activation_callback, command_detector=None):

        self.activation_callback = activation_callback
        self.command_detector = command_detector

        self.speech = SpeechRecognizer(calibrate=False)
        self.recognizer = self.speech.recognizer
        self.microphone = self.speech.microphone

        self.recognizer.energy_threshold = 200
        self.recognizer.dynamic_energy_threshold = True

        self.paused = False

        self.stop_listening = None

        self.cooldown = 2
        self.last_trigger = 0

        self.wake_words = ["omnix", "hey omnix", "hey ommix", "hey om nicks"]
        self.exit_words = ["exit omnix", "shutdown omnix"]

        self._lock = threading.Lock()

    def start(self):

        if self.stop_listening:
            return

        self.paused = False

        try:
            with SpeechRecognizer._mic_lock:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"[WakeListener CALIBRATION ERROR]: {e}")

        print("Wake listener started...")

        self.stop_listening = self.recognizer.listen_in_background(
            self.microphone,
            self._callback,
            phrase_time_limit=5
        )

    def stop(self, wait=True):

        if self.stop_listening:
            try:
                self.stop_listening(wait_for_stop=wait)
                time.sleep(0.2)
            except Exception:
                pass

            self.stop_listening = None

    def _activate(self, exit_requested=False, command_text=None):

        threading.Thread(
            target=self.activation_callback,
            kwargs={
                "exit_requested": exit_requested,
                "command_text": command_text,
            },
            daemon=True
        ).start()

    def _callback(self, recognizer, audio):

        try:

            if self.paused:
                return

            if time.time() - self.last_trigger < self.cooldown:
                return

            with self._lock:
                print("[WakeListener] Processing audio...")

                text = recognizer.recognize_google(audio).lower()

                print(f"[WakeListener] Heard: {text}")

            if any(word in text for word in self.exit_words):

                print("Exit command detected")
                self._activate(exit_requested=True)

                self.last_trigger = time.time()
                return

            if "omnix" not in text:
                if self.command_detector and self.command_detector(text):
                    print("Direct command detected")
                    self._activate(command_text=text)
                    self.last_trigger = time.time()

                return

            if any(word in text for word in self.wake_words):

                print("Omnix wake word detected")

                command_text = self._extract_command_after_wake(text)

                if command_text and self.command_detector and self.command_detector(command_text):
                    self._activate(command_text=command_text)
                else:
                    self._activate()

                self.last_trigger = time.time()

        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(f"[WakeListener ERROR]: {e}")

    def _extract_command_after_wake(self, text):

        wake_markers = [
            "hey omnix",
            "hey ommix",
            "hey om nicks",
            "omnix",
        ]

        for marker in wake_markers:
            if marker in text:
                return text.split(marker, 1)[1].strip(" .,!?:;")

        return ""
