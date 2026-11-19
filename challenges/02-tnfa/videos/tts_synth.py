#!/usr/bin/env python3
"""Synthesise one narration clip with edge-tts and record boundary events.

Usage: tts_synth.py <text_file> <out.mp3> <out.json> [voice]

The JSON holds the boundary events (offset/duration in 100 ns ticks) that the
service emits — SentenceBoundary on current edge-tts, WordBoundary on older
builds — which build.py turns into subtitles.
"""

import asyncio
import json
import sys

import edge_tts


async def main() -> None:
    text = open(sys.argv[1], encoding="utf-8").read()
    mp3_path, json_path = sys.argv[2], sys.argv[3]
    voice = sys.argv[4] if len(sys.argv) > 4 else "en-US-AndrewNeural"
    comm = edge_tts.Communicate(text, voice)
    bounds = []
    with open(mp3_path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"):
                bounds.append({"kind": ch["type"], "offset": ch["offset"],
                               "duration": ch["duration"], "text": ch["text"]})
    json.dump(bounds, open(json_path, "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
