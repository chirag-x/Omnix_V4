# Omnix V4 module
import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1


def record_audio(duration=5):
    """
    Records audio from microphone.
    """
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32"
    )

    sd.wait()

    return np.squeeze(audio)


def record_until_silence(max_duration=10):
    """
    Record audio until silence is detected.
    """
    print("Listening...")

    audio = sd.rec(
        int(max_duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32"
    )

    sd.wait()

    return np.squeeze(audio)