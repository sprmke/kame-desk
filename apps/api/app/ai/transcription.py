import os
import tempfile

from app.services.storage_service import download_object_bytes


def _use_stub_transcription() -> bool:
    if os.environ.get("DOCTORDESK_TESTING") == "1":
        return True
    return os.environ.get("DOCTORDESK_STUB_TRANSCRIPTION", "").lower() in ("1", "true", "yes")


async def transcribe_audio_bytes(audio_bytes: bytes, content_type: str) -> str:
    if _use_stub_transcription():
        return "Patient reports elevated blood pressure. Continue maintenance medications. Follow up in two weeks."

    try:
        from faster_whisper import WhisperModel

        suffix = ".webm"
        if "wav" in content_type:
            suffix = ".wav"
        elif "mpeg" in content_type or "mp3" in content_type:
            suffix = ".mp3"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _info = model.transcribe(tmp.name)
            return " ".join(segment.text.strip() for segment in segments).strip()
    except ImportError:
        return "Transcription unavailable in this environment."


async def transcribe_recording_object(r2_key: str) -> str:
    audio_bytes, content_type = download_object_bytes(r2_key)
    text = await transcribe_audio_bytes(audio_bytes, content_type)
    if not text:
        raise ValueError("Empty transcript")
    return text
