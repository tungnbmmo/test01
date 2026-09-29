"""Clone giọng nói từ file mẫu bằng Coqui XTTS v2 (chạy local, miễn phí).

Ví dụ:
    python -m voice_clone.cli --voice my_voice.wav --text "Xin chào các bạn" -o out.wav
    python -m voice_clone.cli --voice my_voice.wav --text-file script.txt --lang vi -o out.wav
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from .text import split_text

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
# XTTS v2 gốc KHÔNG hỗ trợ tiếng Việt; bản fine-tune cộng đồng này thì có.
VI_REPO = "capleaf/viXTTS"
SAMPLE_RATE = 24000


def prepare_reference(src: Path, workdir: Path) -> Path:
    """Chuyển file mẫu về wav mono 24kHz, bỏ khoảng lặng đầu/cuối (cần ffmpeg)."""
    if not shutil.which("ffmpeg"):
        print("! Không có ffmpeg, dùng nguyên file mẫu (nên là .wav).", file=sys.stderr)
        return src
    dst = workdir / "reference.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-af", "silenceremove=start_periods=1:start_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
         str(dst)],
        check=True, capture_output=True,
    )
    return dst


def write_wav(path: Path, chunks: list[list[float]], pause_s: float) -> None:
    import numpy as np

    gap = np.zeros(int(SAMPLE_RATE * pause_s), dtype=np.float32)
    parts = []
    for c in chunks:
        parts += [np.asarray(c, dtype=np.float32), gap]
    audio = np.clip(np.concatenate(parts), -1.0, 1.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())


def _load_audio(path, sampling_rate=22050):
    """Thay cho TTS load_audio: đọc bằng soundfile, khỏi cần torchcodec/ffmpeg trên Windows."""
    import librosa
    import soundfile
    import torch

    data, sr = soundfile.read(str(path), dtype="float32", always_2d=True)
    data = data.mean(axis=1)
    if sr != sampling_rate:
        data = librosa.resample(data, orig_sr=sr, target_sr=sampling_rate)
    return torch.from_numpy(data).unsqueeze(0).clamp_(-1, 1)


def _clean_vi(text):
    """Chuẩn hóa tối thiểu cho tiếng Việt: viết thường, bỏ ký tự lạ, gọn khoảng trắng."""
    import re

    text = text.lower().replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    text = re.sub(r"[\[\](){}<>*_#@~^|\\/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class Synth:
    """Bọc 2 cách nạp model: XTTS v2 gốc, hoặc checkpoint XTTS trên HuggingFace (vd viXTTS)."""

    def __init__(self, repo, device, ref):
        self.repo = repo
        if repo is None:
            from TTS.api import TTS
            self.tts = TTS(MODEL).to(device)
            self.ref = str(ref)
            return
        from huggingface_hub import snapshot_download
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models import xtts as xtts_module
        from TTS.tts.models.xtts import Xtts

        xtts_module.load_audio = _load_audio
        d = Path(snapshot_download(repo))
        cfg = XttsConfig()
        cfg.load_json(str(d / "config.json"))
        self.model = Xtts.init_from_config(cfg)
        self.model.load_checkpoint(cfg, checkpoint_dir=str(d),
                                   vocab_path=str(d / "vocab.json"), use_deepspeed=False)
        self.model.to(device)
        # coqui-tts chưa có bộ tiền xử lý cho 'vi' -> tự thêm.
        tok, orig = self.model.tokenizer, self.model.tokenizer.preprocess_text
        tok.preprocess_text = lambda txt, lang: _clean_vi(txt) if lang == "vi" else orig(txt, lang)
        self.latent, self.spk = self.model.get_conditioning_latents(audio_path=[str(ref)])

    def say(self, text, lang, speed, temperature):
        if self.repo is None:
            return self.tts.tts(text=text, speaker_wav=self.ref, language=lang,
                                speed=speed, temperature=temperature)
        out = self.model.inference(text, lang, self.latent, self.spk,
                                   temperature=temperature, speed=speed)
        return out["wav"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Clone giọng nói của bạn (XTTS v2)")
    p.add_argument("--voice", required=True, type=Path, help="File giọng mẫu (wav/mp3/m4a...), tốt nhất 10-30s sạch, không nhạc nền")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="Văn bản cần đọc")
    g.add_argument("--text-file", type=Path, help="File .txt chứa văn bản cần đọc")
    p.add_argument("-o", "--output", type=Path, default=Path("voice_output/output.wav"))
    p.add_argument("--lang", default="vi", help="Mã ngôn ngữ: vi, en, ja, zh-cn, ... (mặc định vi)")
    p.add_argument("--max-chars", type=int, default=220, help="Số ký tự tối đa mỗi đoạn")
    p.add_argument("--pause", type=float, default=0.25, help="Khoảng nghỉ giữa các đoạn (giây)")
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--temperature", type=float, default=0.65, help="Thấp = ổn định, cao = biểu cảm hơn")
    p.add_argument("--repo", default=None, help=f"Repo HuggingFace của checkpoint XTTS (mặc định: {VI_REPO} khi --lang vi)")
    p.add_argument("--device", default=None, help="cuda / cpu (mặc định tự nhận)")
    args = p.parse_args(argv)

    if not args.voice.exists():
        p.error(f"Không thấy file giọng mẫu: {args.voice}")
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    chunks = split_text(text, args.max_chars)
    if not chunks:
        p.error("Văn bản trống")

    import torch

    repo = args.repo or (VI_REPO if args.lang == "vi" else None)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Tải model {repo or 'XTTS v2'} trên {device} (lần đầu sẽ tải ~2GB)...")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ref = prepare_reference(args.voice, Path(tmp))
        synth = Synth(repo, device, ref)
        wavs = []
        for i, c in enumerate(chunks, 1):
            print(f"[{i}/{len(chunks)}] {c[:60]}{'...' if len(c) > 60 else ''}")
            wavs.append(synth.say(c, args.lang, args.speed, args.temperature))
    write_wav(args.output, wavs, args.pause)
    print(f"Xong: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
