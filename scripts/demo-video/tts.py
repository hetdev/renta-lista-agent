import json, subprocess, sys
from pathlib import Path
V = Path(__file__).resolve().parent
lines = json.loads((V / "narration.json").read_text())
durations = {}
for item in lines:
    out = V / "raw" / f"narr_{item['id']}.aiff"
    subprocess.run(["say", "-v", "Samantha", "-r", "172", "-o", str(out), item["text"]], check=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                       capture_output=True, text=True, check=True).stdout.strip()
    durations[item["id"]] = float(d)
(V / "durations.json").write_text(json.dumps(durations, indent=2))
total = sum(durations.values())
for k, v in durations.items():
    print(f"{k:>10}: {v:5.1f} s")
print(f"narración total: {total:.1f} s")
