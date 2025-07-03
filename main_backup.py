# transcribe_whisper.py
import numpy as np, sounddevice as sd, whisper

# load the small or medium Whisper model
model = whisper.load_model("small")

# record 10 seconds of audio at 16 kHz
fs = 16_000
print("⏺️  Recording 10 s…")
audio = sd.rec(int(10 * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()
audio = audio.flatten()

# write to a temporary WAV so Whisper can read it
import tempfile, wave
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wf = wave.open(f.name, "wb")
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(fs)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    wf.close()
    path = f.name

# transcribe in Hebrew
result = model.transcribe(path, language="he")
print("Text:", result["text"])
