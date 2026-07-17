#!/usr/bin/env python3
import sys
import os
import tempfile
import subprocess
import asyncio
import edge_tts
import langdetect

# Mapping of language codes to edge-tts voices
VOICES = {
    "it": "it-IT-DiegoNeural",
    "en": "en-GB-RyanNeural",
    "fr": "fr-FR-HenriNeural",
    "es": "es-ES-AlvaroNeural",
    "de": "de-DE-ConradNeural",
}
DEFAULT_VOICE = "en-GB-RyanNeural"

def detect_voice(text):
    try:
        lang = langdetect.detect(text)
        voice = VOICES.get(lang, DEFAULT_VOICE)
        print(f"[tts] Detected language: '{lang}' -> Using voice: {voice}", file=sys.stderr)
        return voice
    except Exception as e:
        print(f"[tts] Language detection failed: {e} -> Using default voice: {DEFAULT_VOICE}", file=sys.stderr)
        return DEFAULT_VOICE

async def run_speak(args):
    if len(args) == 1 and os.path.isfile(args[0]):
        print(f"[tts] Reading input file: {args[0]}", file=sys.stderr)
        try:
            with open(args[0], 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"[tts] Error reading file {args[0]}: {e}", file=sys.stderr)
            return
    elif len(args) > 0:
        text = " ".join(args)
    else:
        text = sys.stdin.read().strip()
        
    if not text:
        print("[tts] No text provided.", file=sys.stderr)
        return

    # Debug snippet of the text
    snippet = text[:60].replace('\n', ' ')
    print(f"[tts] Text to speak: '{snippet}...' ({len(text)} chars)", file=sys.stderr)

    voice = detect_voice(text)
    
    # Create temp file for playback
    fd, temp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    
    try:
        communicate = edge_tts.Communicate(text, voice, rate="-5%")
        await communicate.save(temp_path)
        subprocess.run(["afplay", temp_path], check=True)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

async def run_tts(args):
    if len(args) < 1:
        print("Usage: tts output.mp3 [text/file]", file=sys.stderr)
        sys.exit(1)
        
    output_path = args[0]
    
    if len(args) == 2 and os.path.isfile(args[1]):
        print(f"[tts] Reading input file: {args[1]}", file=sys.stderr)
        try:
            with open(args[1], 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"[tts] Error reading file {args[1]}: {e}", file=sys.stderr)
            sys.exit(1)
    elif len(args) > 1:
        text = " ".join(args[1:])
    else:
        text = sys.stdin.read().strip()
        
    if not text:
        print("Error: No text provided.", file=sys.stderr)
        sys.exit(1)

    # Debug snippet of the text
    snippet = text[:60].replace('\n', ' ')
    print(f"[tts] Text to synthesize: '{snippet}...' ({len(text)} chars)", file=sys.stderr)

    voice = detect_voice(text)
    
    communicate = edge_tts.Communicate(text, voice, rate="-5%")
    await communicate.save(output_path)
    print(f"[tts] Saved to {output_path}", file=sys.stderr)

async def main():
    if len(sys.argv) < 2:
        print("Error: mode (speak/tts) must be specified", file=sys.stderr)
        sys.exit(1)
        
    mode = sys.argv[1]
    args = sys.argv[2:]
    
    if mode == "speak":
        await run_speak(args)
    elif mode == "tts":
        await run_tts(args)
    else:
        print(f"Error: Unknown mode '{mode}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
