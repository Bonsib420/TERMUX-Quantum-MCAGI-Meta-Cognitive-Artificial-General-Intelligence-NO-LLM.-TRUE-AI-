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


REMOTE_BRAIN = "gdrive 666:Quantum Cloud/MCAGI_BRAIN"
REMOTE_BACKUP = "gdrive 666:Quantum Cloud/MCAGI_BACKUP"
WEBDAV_URL = "http://127.0.0.1:8080"
LOCAL_CACHE = os.path.expanduser("~/.quantum-mcagi")


def _run_rclone(args, timeout=600):
    """
    Execute an rclone command and report whether it succeeded along with a short stderr message.
    
    Parameters:
        args (list[str]): Arguments to pass to the rclone binary (do not include the "rclone" command itself).
        timeout (int): Maximum time in seconds to wait for the rclone process before timing out.
    
    Returns:
        tuple[bool, str]: (success, message) where `success` is `True` if rclone exited with status code 0, `False` otherwise; `message` is the stderr output truncated to 200 characters, or a short error token such as "timeout" or "rclone not installed" when applicable.
    """
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
        """
        Initializes a CloudBrain instance, prepares the local cache, and probes rclone/WebDAV availability.
        
        Parameters:
            url (str): Base WebDAV endpoint URL to use for direct HTTP operations; trailing slashes are ignored.
            cache_dir (str): Path to the local directory used for cached cloud files; the directory will be created if it does not exist.
        """
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
        """
        Check whether rclone is installed and whether the configured WebDAV endpoint is reachable, updating availability flags on the instance.
        
        Updates:
        - Sets `self.available` to `True` if running `rclone version` succeeds (exit code 0), `False` otherwise.
        - Sets `self._webdav_active` to `True` if an HTTP GET to `self.url + "/"` returns status 200, `False` otherwise.
        
        Returns:
            bool: `True` if `rclone` is available, `False` otherwise.
        """
        try:
            result = subprocess.run(["rclone", "version"],
                                    capture_output=True, timeout=5)
            self.available = result.returncode == 0
        except:
            self.available = False
        self._webdav_active = False
        if self.available:
            try:
                r = requests.get(self.url + "/", timeout=2)
                self._webdav_active = r.status_code == 200
            except:
                pass
        return self.available

    def _cloud_path(self, relative_path):
        """
        Builds a full WebDAV URL for a path relative to the cloud root.
        
        Parameters:
            relative_path (str): Path relative to the cloud root; leading slashes are ignored.
        
        Returns:
            str: The absolute URL to the resource on the WebDAV server.
        """
        return self.url + "/" + relative_path.lstrip('/')

    def _local_path(self, relative_path):
        """
        Builds the local filesystem path inside the cloud cache corresponding to a given relative cloud path.
        
        Parameters:
            relative_path (str): Path relative to the cloud root; leading slashes are ignored.
        
        Returns:
            str: Path under the configured cache that maps to `relative_path`.
        """
        return os.path.join(self.cache, relative_path.lstrip('/'))

    def startup_pull(self):
        """
        Pull the brain data from the cloud into the instance local cache.
        
        Attempts to copy the configured REMOTE_BRAIN into the CloudBrain cache and prints concise status messages about progress or errors.
        
        Returns:
            True if the copy completed successfully, False otherwise.
        """
        if not self.available:
            print("  ☁ Cloud unavailable — using local cache")
            return False
        print("  ☁ Pulling brain from cloud...")
        ok, err = _run_rclone([
            "copy", REMOTE_BRAIN + "/", self.cache + "/",
            "--update", "--transfers", "4", "--quiet"
        ])
        if ok:
            print("  ☁ Brain loaded from cloud")
        else:
            print(f"  ☁ Pull issue: {err[:80]}")
        return ok

    def shutdown_push(self):
        """
        Pushes the local brain cache directory to the configured cloud remote.
        
        If the cloud client is unavailable, the push is skipped and the function returns False. Otherwise it attempts to copy the cache to the remote (excluding Python bytecode and __pycache__ directories), prints a short status message, and returns the result.
        
        Returns:
            bool: `True` if the remote copy succeeded, `False` otherwise.
        """
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
        """
        Synchronizes the entire brain directory from the configured remote into the local cache.
        
        Performs a full copy from the remote brain location into the instance cache. If the cloud functionality is not available the method does nothing and returns `False`.
        
        Returns:
            bool: `True` if the copy completed successfully, `False` otherwise (includes the case where the cloud is unavailable).
        """
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
        """
        Pushes the local cache directory to the remote brain storage.
        
        Parameters:
        	quiet (bool): If True, suppresses informational and progress output.
        
        Returns:
        	True if the rclone copy completed successfully, False otherwise.
        """
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
        """
        Upload all files from the local cache to the cloud brain remote.
        
        Parameters:
            quiet (bool): If True, suppress progress and informational output.
        
        Returns:
            bool: `True` if the upload completed successfully, `False` otherwise.
        """
        return self.push_all(quiet=quiet)

    def push_state(self):
        """
        Request an asynchronous, rate-limited push of selected state files to the cloud.
        
        If the cloud is unavailable the call returns False. If a push was performed within the last _push_interval seconds the call returns True without starting a new push. Otherwise a daemon thread is started to perform the push in the background and the call returns True.
        
        Returns:
            bool: `True` if a push was scheduled or suppressed by rate limiting, `False` if cloud is not available.
        """
        if not self.available:
            return False
        now = time.time()
        if now - self._last_push < self._push_interval:
            return True
        t = threading.Thread(target=self._do_push_state, daemon=True)
        t.start()
        return True

    def _do_push_state(self):
        """
        Perform a serialized push of selected state files from the local cache to the remote brain and update the last-push timestamp.
        
        Acquires the internal push lock to ensure only one concurrent state push runs, uploads engine_state/**, hilbert/** and *.json files from the cache to REMOTE_BRAIN, and sets self._last_push to the current time.
        """
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
        """
        Create a full backup of the local code directory to the configured backup remote.
        
        Parameters:
        	local_code_dir (str): Path to the local directory to back up. Defaults to the directory containing this module.
        
        Returns:
        	`True` if the backup succeeded, `False` otherwise (including when the cloud is unavailable).
        """
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
        """
        Prints the current cloud synchronization availability and key configuration values.
        
        Displays whether rclone is available, whether the WebDAV endpoint is active, the configured REMOTE_BRAIN and REMOTE_BACKUP remotes, and the local cache directory.
        """
        if not self.available:
            print("  ☁ rclone: NOT AVAILABLE")
            return
        print(f"  ☁ rclone: AVAILABLE")
        print(f"  ☁ WebDAV: {'ACTIVE' if self._webdav_active else 'INACTIVE'}")
        print(f"  ☁ Brain remote: {REMOTE_BRAIN}")
        print(f"  ☁ Backup remote: {REMOTE_BACKUP}")
        print(f"  ☁ Local cache: {self.cache}")

    def download(self, cloud_path, local_path=None):
        """
        Download a file from the cloud to a local path, preferring WebDAV and falling back to rclone.
        
        If `local_path` is omitted, the file is saved into the local cache location corresponding to `cloud_path`. The function ensures the local parent directory exists. When WebDAV is active it attempts an HTTP GET and writes the remote content to `local_path`; WebDAV errors are ignored and the function falls back to using `rclone copyto` from the configured `REMOTE_BRAIN` remote.
        
        Parameters:
            cloud_path (str): Path of the file on the cloud (relative to the remote root).
            local_path (str, optional): Destination filesystem path. If omitted, defaults to the module cache path for `cloud_path`.
        
        Returns:
            bool: `True` if the file was successfully downloaded (via WebDAV or rclone), `False` otherwise.
        """
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
            except:
                pass
        ok, _ = _run_rclone(["copyto", REMOTE_BRAIN + "/" + cloud_path, local_path])
        return ok

    def upload(self, local_path, cloud_path=None):
        """
        Upload a local file to the cloud storage, using WebDAV when available and falling back to rclone.
        
        Parameters:
            local_path (str): Path to the local file to upload.
            cloud_path (str, optional): Destination path in the cloud. If omitted, the destination is:
                - the local path with the cache directory prefix removed if `local_path` is inside the cache, or
                - the basename of `local_path` otherwise.
        
        Returns:
            bool: `True` if the file was uploaded successfully, `False` otherwise.
        """
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
            except:
                pass
        ok, _ = _run_rclone(["copyto", local_path, REMOTE_BRAIN + "/" + cloud_path])
        return ok

    def upload_background(self, local_path, cloud_path=None):
        """
        Starts a daemon thread that uploads a local file to the cloud.
        
        Parameters:
            local_path (str): Filesystem path to the local file to upload.
            cloud_path (str | None): Optional destination path on the cloud; if omitted, the destination is derived from `local_path`.
        """
        t = threading.Thread(target=self.upload, args=(local_path, cloud_path), daemon=True)
        t.start()

    def list_files(self, cloud_dir="/"):
        """
        List entries directly inside a remote WebDAV directory.
        
        Parameters:
            cloud_dir (str): Remote directory path to list (relative to the remote root). Defaults to "/".
        
        Returns:
            list: A list of path strings (hrefs) returned by the WebDAV PROPFIND for the given directory; returns an empty list if WebDAV is inactive or the request/response cannot be parsed.
        """
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
            except:
                pass
        return []

    def exists(self, cloud_path):
        """
        Check whether a resource exists at the given cloud path on the WebDAV endpoint.
        
        Parameters:
            cloud_path (str): Path relative to the remote root (e.g., "dir/file.txt").
        
        Returns:
            `true` if the resource exists (HTTP 200) on the active WebDAV server, `false` otherwise.
        """
        if self._webdav_active:
            try:
                r = requests.head(self._cloud_path(cloud_path), timeout=10)
                return r.status_code == 200
            except:
                pass
        return False

    def wire_engine(self, engine):
        """
        Wire an engine's persistence methods to trigger cloud state pushes after saves.
        
        Replaces the engine's `save_state` and `load_state` methods: `save_state` is wrapped so that, after performing its original save, it triggers `push_state()` on this CloudBrain instance when the cloud is available; `load_state` is replaced with a thin wrapper that delegates to the original loader. Also prints a confirmation message when wiring is complete.
        
        Parameters:
            engine: An object exposing `save_state(path, ...)` and `load_state(path, ...)` methods that will be wrapped in-place.
        """
        _original_save = engine.save_state
        _original_load = engine.load_state
        cloud = self

        @wraps(_original_save)
        def patched_save(path, *args, **kwargs):
            """
            Calls the original save function and triggers a cloud state push when the cloud is available.
            
            Parameters:
                path: Destination path passed to the original save function.
                *args: Positional arguments forwarded to the original save function.
                **kwargs: Keyword arguments forwarded to the original save function.
            
            Returns:
                The value returned by the original save function.
            """
            result = _original_save(path, *args, **kwargs)
            if cloud.available:
                cloud.push_state()
            return result

        @wraps(_original_load)
        def patched_load(path, *args, **kwargs):
            """
            Forward the call to the engine's original load function.
            
            Parameters:
                path (str): Path or identifier to load from.
                *args: Additional positional arguments forwarded to the original loader.
                **kwargs: Additional keyword arguments forwarded to the original loader.
            
            Returns:
                The value returned by the original load function.
            """
            return _original_load(path, *args, **kwargs)

        engine.save_state = patched_save
        engine.load_state = patched_load
        print("  ☁ Engine wired to cloud brain")

    def wire_chat(self):
        """
        Return a pair of callables for integrating cloud synchronization into chat workflows.
        
        The first callable pulls the full remote brain into the local cache; the second schedules a rate-limited background push of incremental state.
        
        Returns:
            tuple: (pull_callable, push_callable) where `pull_callable()` runs a full pull from remote to cache and `push_callable()` requests a background incremental upload.
        """
        return self.pull_all, self.push_state


_instance = None

def get_cloud_brain():
    """
    Provide a module-level singleton CloudBrain instance.
    
    Lazily constructs a CloudBrain on first call and returns the same instance on subsequent calls.
    
    Returns:
        CloudBrain: The shared CloudBrain instance.
    """
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

