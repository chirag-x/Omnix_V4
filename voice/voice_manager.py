import threading
import speech_recognition as sr
import time
from loguru import logger

from voice.tts_engine import OfflineTTS
from voice.speech_recognizer import SpeechRecognizer
from voice.wake_listener import WakeListener
from core.command_processor import CommandProcessor


class VoiceManager:

    def __init__(self, agent_controller):

        self.agent = agent_controller

        self.tts = OfflineTTS()
        self.recognizer = SpeechRecognizer()
        self.command_processor = getattr(
            agent_controller,
            "command_processor",
            CommandProcessor()
        )

        self.wake_listener = WakeListener(
            activation_callback=self._on_wake_detected,
            command_detector=self.command_processor.looks_like_automation
        )

        self.running = True

        self._listening_for_command = False
        self._lock = threading.Lock()

        # Interrupt listener — TTS bolte waqt bhi sun'na ke liye
        self._interrupt_recognizer = sr.Recognizer()
        self._interrupt_recognizer.energy_threshold = 400
        self._interrupt_recognizer.dynamic_energy_threshold = True
        self._interrupt_thread = None

    # ──────────────────────────────────────────────────────────
    # Start
    # ──────────────────────────────────────────────────────────

    def start(self):
        logger.info("VoiceManager starting...")
        self.wake_listener.start()

        # Background interrupt listener start karo
        # self._start_interrupt_listener()

        logger.info("Omnix is waiting for wake word: 'Hey Omnix'")
        print("[Omnix] Sleeping... Say 'Hey Omnix' to wake me up.")

    # ──────────────────────────────────────────────────────────
    # Background interrupt listener
    # TTS bol raha ho tab bhi user ki awaaz detect karo
    # ──────────────────────────────────────────────────────────

    def _start_interrupt_listener(self):

        def listen_for_interrupt():

            mic = self.recognizer.microphone  # 🔥 shared mic

            with mic as source:
                self._interrupt_recognizer.adjust_for_ambient_noise(
                    source, duration=1)

            logger.info("Interrupt listener started")

            def callback(recognizer, audio):
                # Sirf tab kaam karo jab TTS bol raha ho
                if not self.tts.speaking:
                    return

                if self._listening_for_command:
                    return  # 🔥 prevent race condition

                try:
                    text = recognizer.recognize_google(audio).lower()
                    logger.info(f"Interrupt detected during TTS: '{text}'")

                    # Koi bhi awaaz aaye — TTS rok do
                    logger.info("Interrupting TTS...")
                    self.tts.stop_and_flush()

                    # Agar command jaisi lagti hai toh process karo
                    if len(text.split()) >= 2:
                        logger.info(f"Processing interrupt command: {text}")
                        threading.Thread(
                            target=self._handle_interrupt_command,
                            args=(text,),
                            daemon=True
                        ).start()

                except sr.UnknownValueError:
                    # Kuch suna nahi clearly — TTS phir bhi rok do
                    if self.tts.speaking:
                        self.tts.stop_and_flush()
                except Exception as e:
                    logger.debug(f"Interrupt listener error: {e}")

            stop_fn = self._interrupt_recognizer.listen_in_background(
                mic, callback, phrase_time_limit=4
            )
            self._interrupt_stop_fn = stop_fn

            # Thread alive rakhne ke liye
            while self.running:
                threading.Event().wait(1)

        self._interrupt_thread = threading.Thread(
            target=listen_for_interrupt, daemon=True
        )
        self._interrupt_thread.start()

    def _handle_interrupt_command(self, text: str):
        """Interrupt ke baad command process karo"""
        with self._lock:
            if self._listening_for_command:
                return
            self._listening_for_command = True

        try:
            print(f"[User - Interrupt] {text}")
            response = self.agent.process_command(text)
            print(f"[Omnix] {response}")
            if response:
                self.tts.speak(response)
        except Exception as e:
            logger.error(f"Interrupt command error: {e}")
        finally:
            with self._lock:
                self._listening_for_command = False

    # ──────────────────────────────────────────────────────────
    # Wake word callback
    # ──────────────────────────────────────────────────────────

    def _on_wake_detected(self, exit_requested=False, command_text=None):

        if exit_requested:
            logger.info("Exit command received")
            self.speak("Goodbye! Shutting down.")
            self.shutdown()
            return

        with self._lock:
            if self._listening_for_command:
                logger.debug("Already listening, ignoring duplicate wake")
                return
            self._listening_for_command = True

        try:
            if command_text:
                logger.info(f"Direct voice command detected: {command_text}")
            else:
                logger.info("Wake word detected! Listening for command...")
            self.wake_listener.paused = True
            self.wake_listener.stop(wait=True)

            if command_text:
                self.tts.stop_and_flush()
                text = command_text
                print(f"[User] {text}")
                logger.info(f"Command received: {text}")

                response = self.agent.process_command(text)

                print(f"[Omnix] {response}")
                if response:
                    self.speak(response)
                return

            # TTS rok do agar bol raha tha
            # 🔥 stop any previous speech
            self.tts.stop_and_flush()

            time.sleep(0.5)

            self.tts.stop_and_flush()

            time.sleep(0.3)

            self.speak("Yes, I'm listening.")

            # wait for TTS to FULLY finish
            while self.tts.speaking:
                time.sleep(0.1)

            # 🔥 EXTRA stabilization delay
            time.sleep(1.5)

            print("[VoiceManager] Listening for actual command now...")

            time.sleep(0.2)

            text = self._listen_for_user_command()

            if not text:
                logger.info("No command heard after wake word")
                self.speak("No command heard.")
                return

            print(f"[User] {text}")
            logger.info(f"Command received: {text}")

            response = self.agent.process_command(text)

            print(f"[Omnix] {response}")
            if response:
                self.speak(response)

        except Exception as e:
            logger.error(f"Wake handler error: {e}")
            self.speak("Wake handler error:")

        finally:
            try:
                while self.tts.speaking:
                    time.sleep(0.1)

                if self.running:
                    time.sleep(0.2)
                    self.wake_listener.paused = False
                    self.wake_listener.start()

            except Exception as e:
                logger.error(f"Failed to restart wake listener: {e}")

            with self._lock:
                self._listening_for_command = False

    # ──────────────────────────────────────────────────────────
    # Speak helper
    # ──────────────────────────────────────────────────────────

    def _listen_for_user_command(self):

        for attempt in range(2):
            text = self.recognizer.listen_command()

            if not text:
                return None

            if self._looks_like_tts_echo(text):
                logger.info(f"Ignoring likely TTS echo: {text}")

                if attempt == 0:
                    continue

                return None

            return text

        return None

    def _looks_like_tts_echo(self, text):

        text = str(text or "").lower().strip(" .,!?:;")

        echo_phrases = {
            "yes i'm listening",
            "yes i am listening",
            "i'm listening",
            "i am listening",
            "listening",
        }

        return text in echo_phrases

    def speak(self, text: str):
        self.tts.speak(text)

    # ──────────────────────────────────────────────────────────
    # Shutdown
    # ──────────────────────────────────────────────────────────

    def shutdown(self):
        logger.info("VoiceManager shutting down")
        self.running = False
        self.wake_listener.stop(wait=False)
        if hasattr(self, '_interrupt_stop_fn'):
            try:
                self._interrupt_stop_fn(wait_for_stop=False)
            except Exception:
                pass
        self.tts.shutdown()
