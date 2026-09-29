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
    p.add_argument("--device", default=None, help="cuda / cpu (mặc định tự nhận)")
    args = p.parse_args(argv)

    if not args.voice.exists():
        p.error(f"Không thấy file giọng mẫu: {args.voice}")
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8")
    chunks = split_text(text, args.max_chars)
    if not chunks:
        p.error("Văn bản trống")

    import torch
    from TTS.api import TTS

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Tải model XTTS v2 trên {device} (lần đầu sẽ tải ~2GB)...")
    tts = TTS(MODEL).to(device)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        ref = prepare_reference(args.voice, Path(tmp))
        wavs = []
        for i, c in enumerate(chunks, 1):
            print(f"[{i}/{len(chunks)}] {c[:60]}{'...' if len(c) > 60 else ''}")
            wavs.append(tts.tts(text=c, speaker_wav=str(ref), language=args.lang,
                                speed=args.speed, temperature=args.temperature))
    write_wav(args.output, wavs, args.pause)
    print(f"Xong: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
