import json, subprocess
from pathlib import Path
V = Path(__file__).resolve().parent
tl = json.loads((V / "timeline.json").read_text())
dur = json.loads((V / "durations.json").read_text())
video = tl["video"]
out = V.parents[1] / "docs" / "rentalista-demo-live.mp4"
vdur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                            capture_output=True, text=True, check=True).stdout.strip())
marks = [m for m in tl["marks"] if m["id"] in dur]
cmd = ["ffmpeg", "-v", "error", "-y", "-i", video]
chains, labels = [], []
for i, m in enumerate(marks):
    cmd += ["-i", str(V / "raw" / f"narr_{m['id']}.aiff")]
    delay = int(round((m["t"] + 0.25) * 1000))  # small offset: caption appears, then voice
    chains.append(f"[{i+1}:a]aresample=44100,aformat=channel_layouts=mono,adelay={delay}|{delay}[a{i}]")
    labels.append(f"[a{i}]")
n = len(marks)
filt = ";".join(chains) + f";{''.join(labels)}amix=inputs={n}:duration=longest:normalize=0[mix];[mix]volume=1.6,apad[aout]"
cmd += ["-filter_complex", filt, "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "128k", "-ac", "1", "-shortest", "-movflags", "+faststart", str(out)]
subprocess.run(cmd, check=True)
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height",
                       "-of", "default=nw=1", str(out)], capture_output=True, text=True, check=True).stdout
print(f"video webm {vdur:.1f}s -> {out} ({out.stat().st_size/1e6:.1f} MB)")
print(info)
last = max(m["t"] + dur[m["id"]] for m in marks)
print(f"última narración termina en {last:.1f}s de {vdur:.1f}s")
