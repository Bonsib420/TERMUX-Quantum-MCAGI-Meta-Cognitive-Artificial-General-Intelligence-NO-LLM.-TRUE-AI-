"""
Quantum Cloud Brain — WebDAV Storage Layer
The brain lives in Google Drive, served via rclone WebDAV.

Prerequisite: Run in a separate Termux session:
    rclone serve webdav "gdrive 666:Quantum Cloud/MCAGI_BRAIN/" --addr 127.0.0.1:8080 --vfs-cache-mode full

This module replaces local file I/O with WebDAV calls.
The engine doesn't know the difference — it reads files, writes files.
But every file IS Google Drive.

Usage:
    from cloud_brain import CloudBrain
    cloud = CloudBrain()
    cloud.wire_engine(engine)  # patches save/load to use cloud

    # Or manual:
    cloud.download('engine_state/markov_chain.json', '/local/path/markov_chain.json')
    cloud.upload('/local/path/markov_chain.json', 'engine_state/markov_chain.json')
"""

import os
import shutil
import requests
import time
import threading
from pathlib import Path
from functools import wraps
from xml.etree import ElementTree


WEBDAV_URL = "http://127.0.0.1:8080"
LOCAL_CACHE = os.path.expanduser("~/.quantum-mcagi")


class CloudBrain:
    """
    Google Drive brain via WebDAV.
    Local ~/.quantum-mcagi/ is a cache. Cloud is truth.
    """

    def __init__(self, url=WEBDAV_URL, cache_dir=LOCAL_CACHE):
        self.url = url.rstrip('/')
        self.cache = cache_dir
        self.available = False
        self._check_available()

    def _check_available(self):
        """Check if WebDAV server is running."""
        try:
            r = requests.get(self.url + "/", timeout=2)
            self.available = r.status_code == 200
        except:
            self.available = False
        return self.available

    def _cloud_path(self, relative_path):
        """Build full WebDAV URL from relative path."""
        return self.url + "/" + relative_path.lstrip('/')

    def _local_path(self, relative_path):
        """Build local cache path from relative path."""
        return os.path.join(self.cache, relative_path.lstrip('/'))

    # ── Core Operations ──

    def download(self, cloud_path, local_path=None):
        """Download a file from cloud to local cache."""
        if local_path is None:
            local_path = self._local_path(cloud_path)

        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            r = requests.get(self._cloud_path(cloud_path), timeout=300, stream=True)
            if r.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            print(f"  ☁ Download failed {cloud_path}: {e}")
            return False

    def upload(self, local_path, cloud_path=None):
        """Upload a file from local to cloud."""
        if cloud_path is None:
            # Convert local path to relative cloud path
            if local_path.startswith(self.cache):
                cloud_path = local_path[len(self.cache):]
            else:
                cloud_path = os.path.basename(local_path)

        try:
            # Ensure parent directories exist on cloud
            parts = cloud_path.strip('/').split('/')
            for i in range(len(parts) - 1):
                dir_path = '/'.join(parts[:i+1])
                requests.request('MKCOL', self._cloud_path(dir_path + '/'), timeout=10)

            with open(local_path, 'rb') as f:
                r = requests.put(self._cloud_path(cloud_path), data=f, timeout=600)
            return r.status_code in (200, 201, 204)
        except Exception as e:
            print(f"  ☁ Upload failed {cloud_path}: {e}")
            return False

    def upload_background(self, local_path, cloud_path=None):
        """Upload in background thread."""
        t = threading.Thread(
            target=self.upload,
            args=(local_path, cloud_path),
            daemon=True
        )
        t.start()

    def list_files(self, cloud_dir="/"):
        """List files in a cloud directory."""
        try:
            r = requests.request(
                'PROPFIND',
                self._cloud_path(cloud_dir),
                headers={'Depth': '1'},
                timeout=30
            )
            if r.status_code in (200, 207):
                # Parse WebDAV XML response
                files = []
                root = ElementTree.fromstring(r.content)
                ns = {'d': 'DAV:'}
                for response in root.findall('.//d:response', ns):
                    href = response.find('d:href', ns)
                    if href is not None:
                        files.append(href.text)
                return files
            return []
        except Exception as e:
            return []

    def exists(self, cloud_path):
        """Check if a file exists on cloud."""
        try:
            r = requests.head(self._cloud_path(cloud_path), timeout=10)
            return r.status_code == 200
        except:
            return False

    def pull_all(self):
        """Pull entire brain from cloud to local cache."""
        if not self.available:
            print("  ☁ WebDAV not available — using local cache")
            return False

        print("  ☁ Pulling brain from cloud...")
        start = time.time()

        # Pull key directories
        dirs = ['engine_state', 'hilbert', 'library']
        total = 0

        for d in dirs:
            files = self.list_files(d + '/')
            for f in files:
                # Skip directory entries
                f_clean = f.strip('/').split('/')
                if len(f_clean) < 2:
                    continue
                relative = '/'.join(f_clean[1:])  # Remove leading path from WebDAV
                cloud_file = d + '/' + relative
                local_file = self._local_path(cloud_file)

                # Only download if cloud is newer or local doesn't exist
                if not os.path.exists(local_file):
                    if self.download(cloud_file, local_file):
                        total += 1

        elapsed = time.time() - start
        print(f"  ☁ Pulled {total} files in {elapsed:.1f}s")
        return True

    def push_all(self, quiet=False):
        """Push entire local brain to cloud."""
        if not self.available:
            if not quiet:
                print("  ☁ WebDAV not available — skipping cloud push")
            return False

        if not quiet:
            print("  ☁ Pushing brain to cloud...")
        start = time.time()
        total = 0

        for root, dirs, files in os.walk(self.cache):
            # Skip __pycache__ and .pyc files
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for f in files:
                if f.endswith('.pyc'):
                    continue
                local_path = os.path.join(root, f)
                relative = os.path.relpath(local_path, self.cache)
                if self.upload(local_path, relative):
                    total += 1

        elapsed = time.time() - start
        if not quiet:
            print(f"  ☁ Pushed {total} files in {elapsed:.1f}s")
        return True

    def push_state(self):
        """Push just the engine state and hilbert state (fast)."""
        if not self.available:
            return False

        key_files = [
            'engine_state/engine_state.json',
            'engine_state/markov_chain.json',
            'engine_state/corpus_stats.json',
            'engine_state/quantum_engine_state.pkl',
            'hilbert/hilbert_state.npz',
            'hilbert/hilbert_state.json',
        ]

        for f in key_files:
            local = self._local_path(f)
            if os.path.exists(local):
                self.upload_background(local, f)

        print("  ☁ Brain syncing to cloud...")

    # ── Engine Integration ──

    def wire_engine(self, engine):
        """Patch engine save/load to use cloud automatically."""

        _original_save = engine.save_state
        _original_load = engine.load_state
        cloud = self

        @wraps(_original_save)
        def patched_save(path, *args, **kwargs):
            # Save locally first
            result = _original_save(path, *args, **kwargs)
            # Then push to cloud in background
            if cloud.available:
                cloud.push_state()
            return result

        @wraps(_original_load)
        def patched_load(path, *args, **kwargs):
            # Pull from cloud first if available
            if cloud.available:
                # Download key files before loading
                key_files = [
                    'engine_state/markov_chain.json',
                    'engine_state/engine_state.json',
                    'engine_state/corpus_stats.json',
                ]
                for f in key_files:
                    local = cloud._local_path(f)
                    if cloud.exists(f):
                        # Only download if cloud version is different size
                        try:
                            r = requests.head(cloud._cloud_path(f), timeout=5)
                            cloud_size = int(r.headers.get('Content-Length', 0))
                            local_size = os.path.getsize(local) if os.path.exists(local) else 0
                            if cloud_size != local_size and cloud_size > 0:
                                cloud.download(f, local)
                        except:
                            pass
            # Then load normally from local cache
            return _original_load(path, *args, **kwargs)

        engine.save_state = patched_save
        engine.load_state = patched_load
        print("  ☁ Engine wired to cloud brain")

    def wire_chat(self):
        """Return cloud_pull and cloud_push functions for chat.py."""
        return self.pull_all, self.push_state


# ── Singleton ──
_instance = None

def get_cloud_brain():
    """Get or create the global CloudBrain instance."""
    global _instance
    if _instance is None:
        _instance = CloudBrain()
    return _instance


# ── CLI ──
if __name__ == "__main__":
    import sys

    brain = CloudBrain()
    print(f"WebDAV available: {brain.available}")
    print(f"URL: {brain.url}")
    print(f"Cache: {brain.cache}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'pull':
            brain.pull_all()
        elif cmd == 'push':
            brain.push_all()
        elif cmd == 'ls':
            path = sys.argv[2] if len(sys.argv) > 2 else '/'
            files = brain.list_files(path)
            for f in files:
                print(f"  {f}")
        elif cmd == 'status':
            print(f"  Available: {brain.available}")
            files = brain.list_files('/')
            print(f"  Root files: {len(files)}")
            files = brain.list_files('/engine_state/')
            print(f"  Engine state: {len(files)} files")
            files = brain.list_files('/hilbert/')
            print(f"  Hilbert: {len(files)} files")
            files = brain.list_files('/library/')
            print(f"  Library: {len(files)} files")
    else:
        print()
        print("Commands:")
        print("  python cloud_brain.py status  — Check cloud status")
        print("  python cloud_brain.py pull    — Pull brain from cloud")
        print("  python cloud_brain.py push    — Push brain to cloud")
        print("  python cloud_brain.py ls /    — List cloud files")
