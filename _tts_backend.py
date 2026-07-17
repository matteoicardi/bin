#!/usr/bin/env python3
import sys
import os
import tempfile
import subprocess
import asyncio
import re
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

def parse_rate(rate_str):
    rate_str = rate_str.strip().lower()
    
    # Handle multiplier format like 1.5x, 2x, 0.8x
    if rate_str.endswith('x'):
        try:
            val = float(rate_str[:-1])
            percent = int((val - 1.0) * 100)
            sign = "+" if percent >= 0 else ""
            return f"{sign}{percent}%"
        except ValueError:
            pass

    # Handle percentage format like -10%, +5%, 5%
    if rate_str.endswith('%'):
        val_str = rate_str[:-1]
        try:
            # check if it is a valid float
            float(val_str)
            if rate_str[0] in ('+', '-'):
                return rate_str
            else:
                return f"+{rate_str}"
        except ValueError:
            pass
            
    # Handle plain numbers like -10, +5, 5
    try:
        val = float(rate_str)
        # If they input a float like 1.2 or 0.8 without 'x', treat as multiplier
        if 0.1 <= val <= 4.0 and '.' in rate_str:
            percent = int((val - 1.0) * 100)
            sign = "+" if percent >= 0 else ""
            return f"{sign}{percent}%"
        else:
            percent = int(val)
            sign = "+" if percent >= 0 else ""
            return f"{sign}{percent}%"
    except ValueError:
        pass
        
    return None

def format_rate_info(rate):
    try:
        percent = int(rate.replace('%', ''))
        multiplier = 1.0 + (percent / 100.0)
        return f"{rate} ({multiplier:.2f}x speed)"
    except Exception:
        return rate

def detect_voice(text):
    try:
        lang = langdetect.detect(text)
        voice = VOICES.get(lang, DEFAULT_VOICE)
        print(f"[tts] Detected language: '{lang}' -> Using voice: {voice}", file=sys.stderr)
        return voice
    except Exception as e:
        print(f"[tts] Language detection failed: {e} -> Using default voice: {DEFAULT_VOICE}", file=sys.stderr)
        return DEFAULT_VOICE

def split_text(text, max_chars=4000):
    """Splits text into chunks of at most max_chars, preferably at paragraph/sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
        
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If a single paragraph is longer than max_chars, split by sentence
        if len(para) > max_chars:
            # First flush any accumulated chunks
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_len = 0
                
            # Split by sentence endings (., !, ?) followed by whitespace
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if len(sentence) > max_chars:
                    # If a single sentence is larger than max_chars, split it by length
                    words = sentence.split(" ")
                    sub_chunk = []
                    sub_len = 0
                    for word in words:
                        if sub_len + len(word) + 1 > max_chars:
                            chunks.append(" ".join(sub_chunk))
                            sub_chunk = [word]
                            sub_len = len(word)
                        else:
                            sub_chunk.append(word)
                            sub_len += len(word) + 1
                    if sub_chunk:
                        chunks.append(" ".join(sub_chunk))
                else:
                    if current_len + len(sentence) + 1 > max_chars:
                        if current_chunk:
                            chunks.append("\n".join(current_chunk))
                        current_chunk = [sentence]
                        current_len = len(sentence)
                    else:
                        current_chunk.append(sentence)
                        current_len += len(sentence) + 1
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_len = 0
        else:
            if current_len + len(para) + 2 > max_chars:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                current_chunk = [para]
                current_len = len(para)
            else:
                current_chunk.append(para)
                current_len += len(para) + 2
                
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
           
    return chunks

async def audio_producer(chunks, voice, rate, queue):
    for i, chunk in enumerate(chunks):
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        try:
            communicate = edge_tts.Communicate(chunk, voice, rate=rate)
            await communicate.save(temp_path)
            snippet = chunk[:30].replace('\n', ' ')
            await queue.put((temp_path, snippet))
        except Exception as e:
            print(f"\n[tts] Error pre-fetching chunk {i+1}: {e}", file=sys.stderr)
            try:
                os.remove(temp_path)
            except OSError:
                pass
            await queue.put((None, None))
            break
    # Signal completion
    await queue.put((None, None))

async def run_speak(args):
    rate = "-5%"
    text_args = args
    
    if len(args) >= 2:
        parsed = parse_rate(args[-1])
        if parsed is not None:
            rate = parsed
            text_args = args[:-1]
            
    if len(text_args) == 1 and os.path.isfile(text_args[0]):
        print(f"[tts] Reading input file: {text_args[0]}", file=sys.stderr)
        try:
            with open(text_args[0], 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"[tts] Error reading file {text_args[0]}: {e}", file=sys.stderr)
            return
    elif len(text_args) > 0:
        text = " ".join(text_args)
    else:
        text = sys.stdin.read().strip()
        
    if not text:
        print("[tts] No text provided.", file=sys.stderr)
        return

    print(f"[tts] Rate: {format_rate_info(rate)}", file=sys.stderr)

    # Check length
    chunks = split_text(text, max_chars=4000)
    num_chunks = len(chunks)
    
    if num_chunks == 1:
        snippet = text[:60].replace('\n', ' ')
        print(f"[tts] Text to speak: '{snippet}...' ({len(text)} chars)", file=sys.stderr)
        voice = detect_voice(text)
        
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(temp_path)
            subprocess.run(["afplay", temp_path], check=True)
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
    else:
        print(f"[tts] Document is long ({len(text)} chars). Split into {num_chunks} chunks for smooth streaming playback.", file=sys.stderr)
        voice = detect_voice(text)
        queue = asyncio.Queue(maxsize=1)
        
        # Start producer in the background
        producer_task = asyncio.create_task(audio_producer(chunks, voice, rate, queue))
        
        try:
            for i in range(num_chunks):
                temp_path, snippet = await queue.get()
                if temp_path is None:
                    break
                    
                print(f"[tts] Playing chunk {i+1}/{num_chunks}: '{snippet}...' ", file=sys.stderr)
                try:
                    proc = await asyncio.create_subprocess_exec("afplay", temp_path)
                    await proc.wait()
                finally:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
        finally:
            producer_task.cancel()
            while not queue.empty():
                try:
                    temp_path, _ = queue.get_nowait()
                    if temp_path:
                        os.remove(temp_path)
                except Exception:
                    pass

async def run_tts(args):
    if len(args) < 1:
        print("Usage: tts output.mp3 [text/file] [rate]", file=sys.stderr)
        sys.exit(1)
        
    output_path = args[0]
    
    rate = "-5%"
    text_args = args[1:]
    
    if len(args[1:]) >= 2:
        parsed = parse_rate(args[-1])
        if parsed is not None:
            rate = parsed
            text_args = args[1:-1]
            
    if len(text_args) == 1 and os.path.isfile(text_args[0]):
        print(f"[tts] Reading input file: {text_args[0]}", file=sys.stderr)
        try:
            with open(text_args[0], 'r', encoding='utf-8') as f:
                text = f.read().strip()
        except Exception as e:
            print(f"[tts] Error reading file {text_args[0]}: {e}", file=sys.stderr)
            sys.exit(1)
    elif len(text_args) > 0:
        text = " ".join(text_args)
    else:
        text = sys.stdin.read().strip()
        
    if not text:
        print("Error: No text provided.", file=sys.stderr)
        sys.exit(1)

    print(f"[tts] Rate: {format_rate_info(rate)}", file=sys.stderr)

    chunks = split_text(text, max_chars=4000)
    num_chunks = len(chunks)
    
    if num_chunks == 1:
        snippet = text[:60].replace('\n', ' ')
        print(f"[tts] Text to synthesize: '{snippet}...' ({len(text)} chars)", file=sys.stderr)
        voice = detect_voice(text)
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_path)
        print(f"[tts] Saved to {output_path}", file=sys.stderr)
    else:
        print(f"[tts] Document is long ({len(text)} chars). Splitting into {num_chunks} chunks to avoid API size limits.", file=sys.stderr)
        voice = detect_voice(text)
        
        with open(output_path, 'wb') as outfile:
            for i, chunk in enumerate(chunks):
                snippet = chunk[:30].replace('\n', ' ')
                print(f"[tts] Synthesizing chunk {i+1}/{num_chunks}: '{snippet}...' ", file=sys.stderr)
                
                fd, temp_path = tempfile.mkstemp(suffix=".mp3")
                os.close(fd)
                try:
                    communicate = edge_tts.Communicate(chunk, voice, rate=rate)
                    await communicate.save(temp_path)
                    with open(temp_path, 'rb') as infile:
                        outfile.write(infile.read())
                finally:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                        
        print(f"[tts] All chunks combined and saved to {output_path}", file=sys.stderr)

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
