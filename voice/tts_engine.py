import asyncio
import edge_tts
import threading
import queue
import os
import uuid
import pygame
import re
from loguru import logger


class OfflineTTS:

    def __init__(self):

        self.queue = queue.Queue()
        self.running = True
        self.speaking = False          # True jab TTS bol raha ho
        self._interrupted = False      # NEW — interrupt flag

        pygame.mixer.init()

        self.voice = "en-US-AriaNeural"
        self.loop = asyncio.new_event_loop()

        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    # ──────────────────────────────────────────────────────────
    # Speak — text queue mein daalo
    # ──────────────────────────────────────────────────────────

    def speak(self, text: str):
        cleaned = re.sub(r"\*.*?\*", "", text)
        cleaned = re.sub(r"^omnix\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        if cleaned:
            self.queue.put(cleaned)

    # ──────────────────────────────────────────────────────────
    # Stop — beech mein roko aur queue saaf karo
    # ──────────────────────────────────────────────────────────

    def stop_current(self):
        """TTS turant band karo — interrupt flag set karo"""
        if self.speaking:
            logger.info("TTS interrupted by user")
            self._interrupted = True
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def flush(self):
        """Queue mein baaki saare pending messages hata do"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Exception:
                break

    def stop_and_flush(self):
        """Ek saath stop + flush — voice_manager se call hoga"""
        self.stop_current()
        self.flush()

    # ──────────────────────────────────────────────────────────
    # Worker thread
    # ──────────────────────────────────────────────────────────

    def _worker(self):

        asyncio.set_event_loop(self.loop)

        while self.running:

            try:
                text = self.queue.get(timeout=1)
            except queue.Empty:
                continue

            if text is None:
                break

            filename = None

            try:
                self.speaking = True
                self._interrupted = False

                logger.info(f"TTS speaking: {text[:60]}...")

                filename = f"temp_{uuid.uuid4().hex}.mp3"

                # Audio generate karo
                self.loop.run_until_complete(
                    self._generate_audio(text, filename)
                )

                # Agar generate ke dauran interrupt aaya toh skip karo
                if self._interrupted:
                    logger.info("TTS skipped (interrupted before playback)")
                    continue

                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                # Play loop — interrupt check karte raho
                while pygame.mixer.music.get_busy():
                    if self._interrupted:
                        pygame.mixer.music.stop()
                        logger.info("TTS playback stopped mid-sentence")
                        break
                    pygame.time.Clock().tick(20)

                pygame.mixer.music.unload()

            except Exception as e:
                logger.error(f"TTS error: {e}")

            finally:
                # File cleanup
                if filename and os.path.exists(filename):
                    try:
                        os.remove(filename)
                    except Exception:
                        pass

                self.speaking = False
                self._interrupted = False

                try:
                    self.queue.task_done()
                except Exception:
                    pass

    async def _generate_audio(self, text: str, filename: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filename)

    # ──────────────────────────────────────────────────────────
    # Shutdown
    # ──────────────────────────────────────────────────────────

    def shutdown(self):
        self.running = False
        self.stop_current()
        self.queue.put(None)
        try:
            pygame.mixer.quit()
        except Exception:
            pass