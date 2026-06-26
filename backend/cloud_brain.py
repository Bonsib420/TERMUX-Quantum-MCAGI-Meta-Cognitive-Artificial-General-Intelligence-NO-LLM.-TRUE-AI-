"""
Quantum Cloud Brain
The brain lives in Google Drive. Local storage is cache only.

Two modes:
  1. rclone direct — terminal sync (pull/push via rclone copy)
  2. WebDAV — frontend access (rclone serve webdav in separate session)

Google Drive structure:
  Quantum Cloud/
    MCAGI_BRAIN/    — brain data (Markov, Hilbert, concepts, library)
    MCAGI_BACKUP/   — full system (code + brain + docs)

Usage:
    from cloud_brain import CloudBrain
    cloud = CloudBrain()
    cloud.startup_pull()       # on startup
    cloud.shutdown_push()      # on quit
    cloud.push_all()           # manual full push
    cloud.backup_full_system() # code + brain backup
"""

import os
import subprocess
import time
import threading
import requests
from pathlib import Path
from functools import wraps
from xml.etree import ElementTree


# rclone remote name. Override with QMCAGI_RCLONE_REMOTE if your remote is named
# differently (e.g. "gdrive666"). Default keeps the historical "gdrive 666".
RCLONE_REMOTE = os.environ.get("QMCAGI_RCLONE_REMOTE", "gdrive 666")
REMOTE_BRAIN = f"{RCLONE_REMOTE}:Quantum Cloud/BACKUPS/3_Frontend_QuantumBrain_L_R"
REMOTE_BACKUP = f"{RCLONE_REMOTE}:Quantum Cloud/MCAGI_BACKUP"
WEBDAV_URL = "http://127.0.0.1:8080"
LOCAL_CACHE = os.path.expanduser("~/.quantum-mcagi")


def _run_rclone(args, timeout=600):
    try:
        result = subprocess.run(
            ["rclone"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stderr[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "rclone not installed"
    except Exception as e:
        return False, str(e)


class CloudBrain:

    def __init__(self, url=WEBDAV_URL, cache_dir=LOCAL_CACHE):
        self.url = url.rstrip('/')
        self.cache = cache_dir
        self.available = False
        self._webdav_active = False
        self._push_lock = threading.Lock()
        self._last_push = 0
        self._push_interval = 60
        os.makedirs(self.cache, exist_ok=True)
        self._check_available()

    def _check_available(self):
        try:
            result = subprocess.run(["rclone", "version"],
                                    capture_output=True, timeout=5)
            self.available = result.returncode == 0
        except Exception:
            self.available = False
        self._webdav_active = False
        if self.available:
            try:
                r = requests.get(self.url + "/", timeout=2)
                self._webdav_active = r.status_code == 200
            except Exception:
                pass
        return self.available

    def _cloud_path(self, relative_path):
        return self.url + "/" + relative_path.lstrip('/')

    def _local_path(self, relative_path):
        return os.path.join(self.cache, relative_path.lstrip('/'))

    def startup_pull(self):
        if not self.available:
            print("  ☁ Cloud unavailable — using local cache")
            return False
        print("  ☁ Pulling brain from cloud...")
        ok, err = _run_rclone([
            "copy", REMOTE_BRAIN + "/", self.cache + "/",
            "--update", "--transfers", "4", "--quiet",
            "--exclude", "growth.json",
            "--exclude", "user_settings.json",
            "--exclude", "analyzer_scores.json",
            "--exclude", "session_state.json",
            "--exclude", "engine_state/engine_state.json",
        ])
        if ok:
            print("  ☁ Brain loaded from cloud")
        else:
            print(f"  ☁ Pull issue: {err[:80]}")
        return ok

    def shutdown_push(self):
        if not self.available:
            print("  ☁ Cloud unavailable — changes cached locally")
            return False
        print("  ☁ Pushing brain to cloud...")
        ok, err = _run_rclone([
            "copy", self.cache + "/", REMOTE_BRAIN + "/",
            "--update", "--transfers", "4",
            "--exclude", "__pycache__/**",
            "--exclude", "*.pyc", "--quiet"
        ])
        if ok:
            print("  ☁ Brain saved to cloud")
        else:
            print(f"  ☁ Push issue: {err[:80]}")
        return ok

    def pull_all(self):
        if not self.available:
            print("  ☁ Cloud unavailable — using local cache")
            return False
        print("  ☁ Pulling full brain from cloud...")
        ok, err = _run_rclone([
            "copy", REMOTE_BRAIN + "/", self.cache + "/",
            "--transfers", "4", "--progress"
        ])
        if ok:
            print("  ☁ Full brain loaded from cloud")
        else:
            print(f"  ☁ Pull error: {err[:80]}")
        return ok

    def push_all(self, quiet=False):
        if not self.available:
            if not quiet:
                print("  ☁ Cloud unavailable — skipping push")
            return False
        if not quiet:
            print("  ☁ Pushing brain to cloud...")
        ok, err = _run_rclone([
            "copy", self.cache + "/", REMOTE_BRAIN + "/",
            "--update", "--transfers", "4",
            "--exclude", "__pycache__/**",
            "--exclude", "*.pyc", "--progress"
        ])
        if ok and not quiet:
            print("  ☁ Brain synced to cloud")
        elif not ok and not quiet:
            print(f"  ☁ Push error: {err[:80]}")
        return ok

    def upload_all(self, quiet=False):
        return self.push_all(quiet=quiet)

    def push_state(self):
        if not self.available:
            return False
        now = time.time()
        if now - self._last_push < self._push_interval:
            return True
        t = threading.Thread(target=self._do_push_state, daemon=True)
        t.start()
        return True

    def _do_push_state(self):
        with self._push_lock:
            _run_rclone([
                "copy", self.cache + "/", REMOTE_BRAIN + "/",
                "--update", "--transfers", "2",
                "--include", "engine_state/**",
                "--include", "hilbert/**",
                "--include", "*.json",
                "--quiet"
            ])
            self._last_push = time.time()

    def backup_full_system(self, local_code_dir=None):
        if local_code_dir is None:
            local_code_dir = os.path.dirname(os.path.abspath(__file__))
        if not self.available:
            print("  ☁ Cloud unavailable — cannot backup")
            return False
        print("  ☁ Backing up full system to cloud...")
        ok, err = _run_rclone([
            "copy", local_code_dir, REMOTE_BACKUP + "/",
            "--exclude", "__pycache__/**",
            "--exclude", "*.pyc",
            "--transfers", "4", "--progress"
        ])
        if ok:
            print(f"  ☁ Full system backed up to {REMOTE_BACKUP}")
        else:
            print(f"  ☁ Backup error: {err[:80]}")
        return ok

    def cloud_status(self):
        if not self.available:
            print("  ☁ rclone: NOT AVAILABLE")
            return
        print(f"  ☁ rclone: AVAILABLE")
        print(f"  ☁ WebDAV: {'ACTIVE' if self._webdav_active else 'INACTIVE'}")
        print(f"  ☁ Brain remote: {REMOTE_BRAIN}")
        print(f"  ☁ Backup remote: {REMOTE_BACKUP}")
        print(f"  ☁ Local cache: {self.cache}")

    def download(self, cloud_path, local_path=None):
        if local_path is None:
            local_path = self._local_path(cloud_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if self._webdav_active:
            try:
                r = requests.get(self._cloud_path(cloud_path), timeout=300, stream=True)
                if r.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
            except Exception:
                pass
        ok, _ = _run_rclone(["copyto", REMOTE_BRAIN + "/" + cloud_path, local_path])
        return ok

    def upload(self, local_path, cloud_path=None):
        if cloud_path is None:
            if local_path.startswith(self.cache):
                cloud_path = local_path[len(self.cache):]
            else:
                cloud_path = os.path.basename(local_path)
        if self._webdav_active:
            try:
                parts = cloud_path.strip('/').split('/')
                for i in range(len(parts) - 1):
                    dir_path = '/'.join(parts[:i+1])
                    requests.request('MKCOL', self._cloud_path(dir_path + '/'), timeout=10)
                with open(local_path, 'rb') as f:
                    r = requests.put(self._cloud_path(cloud_path), data=f, timeout=600)
                return r.status_code in (200, 201, 204)
            except Exception:
                pass
        ok, _ = _run_rclone(["copyto", local_path, REMOTE_BRAIN + "/" + cloud_path])
        return ok

    def upload_background(self, local_path, cloud_path=None):
        t = threading.Thread(target=self.upload, args=(local_path, cloud_path), daemon=True)
        t.start()

    def list_files(self, cloud_dir="/"):
        if self._webdav_active:
            try:
                r = requests.request('PROPFIND', self._cloud_path(cloud_dir),
                                     headers={'Depth': '1'}, timeout=30)
                if r.status_code in (200, 207):
                    files = []
                    root = ElementTree.fromstring(r.content)
                    ns = {'d': 'DAV:'}
                    for response in root.findall('.//d:response', ns):
                        href = response.find('d:href', ns)
                        if href is not None:
                            files.append(href.text)
                    return files
            except Exception:
                pass
        return []

    def exists(self, cloud_path):
        if self._webdav_active:
            try:
                r = requests.head(self._cloud_path(cloud_path), timeout=10)
                return r.status_code == 200
            except Exception:
                pass
        return False

    def wire_engine(self, engine):
        _original_save = engine.save_state
        _original_load = engine.load_state
        cloud = self

        @wraps(_original_save)
        def patched_save(path, *args, **kwargs):
            result = _original_save(path, *args, **kwargs)
            if cloud.available:
                cloud.push_state()
            return result

        @wraps(_original_load)
        def patched_load(path, *args, **kwargs):
            return _original_load(path, *args, **kwargs)

        engine.save_state = patched_save
        engine.load_state = patched_load
        print("  ☁ Engine wired to cloud brain")

    def wire_chat(self):
        return self.pull_all, self.push_state


_instance = None

def get_cloud_brain():
    global _instance
    if _instance is None:
        _instance = CloudBrain()
    return _instance


if __name__ == "__main__":
    import sys
    brain = CloudBrain()
    print(f"rclone available: {brain.available}")
    print(f"WebDAV active: {brain._webdav_active}")
    print(f"Cache: {brain.cache}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'pull':
            brain.pull_all()
        elif cmd == 'push':
            brain.push_all()
        elif cmd == 'backup':
            brain.backup_full_system()
        elif cmd == 'status':
            brain.cloud_status()
    else:
        print()
        print("Commands:")
        print("  python cloud_brain.py pull    — Pull brain from cloud")
        print("  python cloud_brain.py push    — Push brain to cloud")
        print("  python cloud_brain.py backup  — Full system backup")
        print("  python cloud_brain.py status  — Cloud status")

