#!/usr/bin/env python3
"""
Quantum MCAGI — YouTube Channel Transcript Ingester
Downloads auto-generated subtitles from YouTube channels/playlists
and feeds them into the engine. No video download. Text only.

Usage:
    python youtube_ingest.py CHANNEL_URL              # Latest 50 videos
    python youtube_ingest.py CHANNEL_URL --max 100    # Latest 100
    python youtube_ingest.py CHANNEL_URL --all        # Everything
    python youtube_ingest.py --batch channels.txt     # Multiple channels
    python youtube_ingest.py --dry-run CHANNEL_URL    # List videos only
"""

import subprocess
import os
import sys
import json
import re
import time
import glob
from datetime import datetime

# Config
SUB_DIR = os.path.expanduser('~/.quantum-mcagi/youtube_subs')
CHECKPOINT = os.path.expanduser('~/.quantum-mcagi/youtube_checkpoint.json')
os.makedirs(SUB_DIR, exist_ok=True)


def load_checkpoint():
    if os.path.exists(CHECKPOINT):
        try:
            with open(CHECKPOINT, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'completed': [], 'failed': [], 'stats': {}}


def save_checkpoint(cp):
    with open(CHECKPOINT, 'w') as f:
        json.dump(cp, f, indent=2)


def get_video_list(channel_url, max_videos=50):
    """Get list of video URLs from a channel."""
    print(f"  Fetching video list from {channel_url}...")
    
    cmd = [
        'yt-dlp', '--flat-playlist', '--print', '%(id)s\t%(title)s',
        '--playlist-end', str(max_videos),
        channel_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos = []
        for line in result.stdout.strip().split('\n'):
            if '\t' in line:
                vid_id, title = line.split('\t', 1)
                videos.append({
                    'id': vid_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={vid_id}'
                })
            elif line.strip():
                videos.append({
                    'id': line.strip(),
                    'title': 'Unknown',
                    'url': f'https://www.youtube.com/watch?v={line.strip()}'
                })
        return videos
    except subprocess.TimeoutExpired:
        print("  Timeout fetching video list")
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def download_subtitles(video_url, video_id):
    """Download auto-generated subtitles for a video."""
    output_path = os.path.join(SUB_DIR, video_id)
    
    # Check if already downloaded
    existing = glob.glob(f"{output_path}*.srt") + glob.glob(f"{output_path}*.vtt")
    if existing:
        return existing[0]
    
    cmd = [
        'yt-dlp',
        '--write-auto-sub',
        '--sub-lang', 'en',
        '--skip-download',
        '--convert-subs', 'srt',
        '-o', output_path,
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Find the downloaded subtitle file
        srt_files = glob.glob(f"{output_path}*.srt")
        if srt_files:
            return srt_files[0]
        
        vtt_files = glob.glob(f"{output_path}*.vtt")
        if vtt_files:
            return vtt_files[0]
        
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None


def clean_srt(filepath):
    """Extract plain text from SRT subtitle file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Remove SRT formatting
        # Remove sequence numbers
        content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
        # Remove timestamps
        content = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', content)
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        # Remove duplicate lines (auto-subs repeat a lot)
        lines = content.split('\n')
        seen = set()
        cleaned = []
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                cleaned.append(line)
        
        text = ' '.join(cleaned)
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    except Exception as e:
        return None


def feed_to_engine(text, video_title=""):
    """Feed cleaned transcript text to the MCAGI engine."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from quantum_language_engine import QuantumLanguageEngine
        
        # Use existing engine if available
        if not hasattr(feed_to_engine, '_engine'):
            feed_to_engine._engine = QuantumLanguageEngine()
            state_dir = os.path.expanduser('~/.quantum-mcagi/engine_state')
            if os.path.exists(state_dir):
                feed_to_engine._engine.load_state(state_dir)
            
            # Wire Hilbert if available
            try:
                from hilbert_bridge import wire_hilbert
                wire_hilbert(feed_to_engine._engine)
            except:
                pass
        
        engine = feed_to_engine._engine
        engine.learn_from_text(text)
        return len(text.split())
    except Exception as e:
        print(f"    Engine error: {e}")
        return 0


def ingest_channel(channel_url, max_videos=50, dry_run=False, feed=True):
    """Download and ingest all subtitles from a YouTube channel."""
    
    # Extract channel name from URL
    channel_name = channel_url.split('/')[-1].replace('@', '')
    
    print(f"\n  ╔══ YOUTUBE CHANNEL INGESTION ══════════════════════")
    print(f"  ║ Channel: {channel_name}")
    print(f"  ║ Max videos: {max_videos}")
    
    videos = get_video_list(channel_url, max_videos)
    print(f"  ║ Videos found: {len(videos)}")
    
    if dry_run:
        print(f"  ║ DRY RUN — listing only")
        print(f"  ╠═══════════════════════════════════════════════════")
        for i, v in enumerate(videos, 1):
            print(f"  ║ {i:3d}. {v['title'][:60]}")
        print(f"  ╚═══════════════════════════════════════════════════")
        return
    
    checkpoint = load_checkpoint()
    completed_ids = set(checkpoint['completed'])
    
    print(f"  ║ Previously completed: {len(completed_ids & set(v['id'] for v in videos))}")
    print(f"  ╠═══════════════════════════════════════════════════")
    
    success = 0
    failed = 0
    total_words = 0
    start_time = time.time()
    
    for i, video in enumerate(videos, 1):
        if video['id'] in completed_ids:
            continue
        
        title_short = video['title'][:50]
        print(f"  ║ [{i}/{len(videos)}] {title_short}...")
        
        # Download subtitles
        sub_file = download_subtitles(video['url'], video['id'])
        
        if not sub_file:
            print(f"  ║   ✗ No subtitles available")
            failed += 1
            checkpoint['failed'].append(video['id'])
            save_checkpoint(checkpoint)
            continue
        
        # Clean and extract text
        text = clean_srt(sub_file)
        
        if not text or len(text) < 50:
            print(f"  ║   ✗ Subtitle too short or empty")
            failed += 1
            continue
        
        words = len(text.split())
        
        if feed:
            fed = feed_to_engine(text, video['title'])
            total_words += fed
            print(f"  ║   ✓ {words:,} words fed to engine")
        else:
            total_words += words
            print(f"  ║   ✓ {words:,} words extracted")
        
        success += 1
        checkpoint['completed'].append(video['id'])
        
        # Save checkpoint every 5 videos
        if success % 5 == 0:
            save_checkpoint(checkpoint)
            if feed and hasattr(feed_to_engine, '_engine'):
                try:
                    state_dir = os.path.expanduser('~/.quantum-mcagi/engine_state')
                    feed_to_engine._engine.save_state(state_dir)
                    print(f"  ║   💾 Engine state saved")
                except:
                    pass
        
        # Rate limit to avoid YouTube throttling
        time.sleep(1)
    
    elapsed = time.time() - start_time
    
    # Final save
    save_checkpoint(checkpoint)
    if feed and hasattr(feed_to_engine, '_engine'):
        try:
            state_dir = os.path.expanduser('~/.quantum-mcagi/engine_state')
            feed_to_engine._engine.save_state(state_dir)
        except:
            pass
    
    # Update stats
    if channel_name not in checkpoint['stats']:
        checkpoint['stats'][channel_name] = {'videos': 0, 'words': 0}
    checkpoint['stats'][channel_name]['videos'] += success
    checkpoint['stats'][channel_name]['words'] += total_words
    save_checkpoint(checkpoint)
    
    print(f"  ╠═══════════════════════════════════════════════════")
    print(f"  ║ COMPLETE: {channel_name}")
    print(f"  ║ Successful: {success}/{len(videos)}")
    print(f"  ║ Failed: {failed}")
    print(f"  ║ Words ingested: {total_words:,}")
    print(f"  ║ Time: {elapsed/60:.1f} minutes")
    print(f"  ╚═══════════════════════════════════════════════════\n")


def ingest_batch(channels_file):
    """Ingest multiple channels from a text file."""
    with open(channels_file, 'r') as f:
        channels = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"\n  Batch ingestion: {len(channels)} channels")
    
    for channel in channels:
        try:
            ingest_channel(channel, max_videos=50)
        except Exception as e:
            print(f"  Error on {channel}: {e}")
            continue


# ── CLI ──

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Quantum MCAGI — YouTube Channel Transcript Ingester")
        print()
        print("Usage:")
        print("  python youtube_ingest.py CHANNEL_URL              # Latest 50")
        print("  python youtube_ingest.py CHANNEL_URL --max 100    # Latest 100")
        print("  python youtube_ingest.py CHANNEL_URL --all        # All videos")
        print("  python youtube_ingest.py --batch channels.txt     # Multiple")
        print("  python youtube_ingest.py --dry-run CHANNEL_URL    # List only")
        print("  python youtube_ingest.py --stats                  # Show stats")
        sys.exit(0)
    
    # Stats
    if '--stats' in sys.argv:
        cp = load_checkpoint()
        print(f"\n  Completed videos: {len(cp['completed'])}")
        print(f"  Failed: {len(cp['failed'])}")
        for ch, stats in cp.get('stats', {}).items():
            print(f"  {ch}: {stats['videos']} videos, {stats['words']:,} words")
        sys.exit(0)
    
    # Batch mode
    if '--batch' in sys.argv:
        idx = sys.argv.index('--batch')
        if idx + 1 < len(sys.argv):
            ingest_batch(sys.argv[idx + 1])
        sys.exit(0)
    
    # Dry run
    dry_run = '--dry-run' in sys.argv
    
    # Max videos
    max_videos = 50
    if '--max' in sys.argv:
        idx = sys.argv.index('--max')
        if idx + 1 < len(sys.argv):
            max_videos = int(sys.argv[idx + 1])
    if '--all' in sys.argv:
        max_videos = 9999
    
    # Get channel URL (first non-flag argument)
    channel_url = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and ('youtube.com' in arg or 'youtu.be' in arg):
            channel_url = arg
            break
    
    if not channel_url:
        print("No YouTube URL provided")
        sys.exit(1)
    
    ingest_channel(channel_url, max_videos=max_videos, dry_run=dry_run)
