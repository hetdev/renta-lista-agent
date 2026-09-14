# Demo video (live recording)

Records the public demo with Playwright (real browser, visible cursor, on-page captions) and mixes an English
narration generated with macOS `say` (voice Samantha). Output: `docs/rentalista-demo-live.mp4` (gitignored).

```bash
cd scripts/demo-video
python3 tts.py                 # narration.json -> raw/narr_*.aiff + durations.json
node record.js                 # drives https://deuhmh4dvlr6i.cloudfront.net/en/, writes raw/*.webm + timeline.json
python3 mux.py                 # webm + narration -> ../../docs/rentalista-demo-live.mp4 (h264/aac, 1280x720)
```

Requirements: Node 22, Playwright 1.63 with its Chromium, ffmpeg, macOS `say`. Edit `narration.json` to change
the voice-over; captions and scene order live in `record.js`. Keep the video under 5:00 for Devpost.
