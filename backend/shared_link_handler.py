"""
🔗 QUANTUM AI - SHARED LINK HANDLER
====================================

Process files from shared cloud links:
- Google Drive
- Dropbox  
- OneDrive
- Direct file URLs

ARTICLE 2 - Universal Explorer: Access data from anywhere
"""

import requests
import os
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
import re


class SharedLinkHandler:
    """
    Handle file downloads from shared cloud links
    """
    
    def __init__(self):
        # Use environment variable or default to local writable directory
        self.download_dir = os.environ.get(
            "UPLOAD_DIR", 
            os.path.expanduser("~/.quantum-mcagi-backend/uploads")
        )
        try:
            os.makedirs(self.download_dir, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create upload directory {self.download_dir}: {e}")
            # Fallback to /tmp
            self.download_dir = "/tmp/quantum-uploads"
            os.makedirs(self.download_dir, exist_ok=True)
    
    def detect_link_type(self, url: str) -> str:
        """Detect what type of shared link this is"""
        url_lower = url.lower()
        
        if 'drive.google.com' in url_lower:
            return 'google_drive'
        elif 'dropbox.com' in url_lower:
            return 'dropbox'
        elif 'onedrive' in url_lower or '1drv.ms' in url_lower:
            return 'onedrive'
        elif url_lower.startswith('http'):
            return 'direct'
        else:
            return 'unknown'
    
    def convert_to_direct_link(self, url: str, link_type: str) -> Optional[str]:
        """Convert shared link to direct download link"""
        
        if link_type == 'google_drive':
            # Google Drive: extract file ID and convert to download link
            # Formats:
            # https://drive.google.com/file/d/FILE_ID/view
            # https://drive.google.com/open?id=FILE_ID
            
            file_id = None
            
            # Try pattern 1: /file/d/FILE_ID/
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
            
            # Try pattern 2: ?id=FILE_ID
            if not file_id:
                match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
                if match:
                    file_id = match.group(1)
            
            if file_id:
                return f"https://drive.google.com/uc?export=download&id={file_id}"
        
        elif link_type == 'dropbox':
            # Dropbox: change dl=0 to dl=1
            if '?dl=0' in url:
                return url.replace('?dl=0', '?dl=1')
            elif '?dl=1' not in url:
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}dl=1"
            return url
        
        elif link_type == 'onedrive':
            # OneDrive: convert to direct download
            # This is more complex, might need specific handling
            if 'embed' in url:
                return url.replace('embed', 'download')
            # For 1drv.ms short links, direct download might work
            return url
        
        elif link_type == 'direct':
            return url
        
        return None
    
    async def download_from_link(self, url: str, filename: Optional[str] = None) -> Dict:
        """
        Download file from shared link
        """
        try:
            # Detect link type
            link_type = self.detect_link_type(url)
            
            if link_type == 'unknown':
                return {
                    "status": "error",
                    "message": "Unknown link type. Supported: Google Drive, Dropbox, OneDrive, direct URLs"
                }
            
            # Convert to direct download link
            download_url = self.convert_to_direct_link(url, link_type)
            
            if not download_url:
                return {
                    "status": "error",
                    "message": f"Could not convert {link_type} link to direct download"
                }
            
            # Download the file
            print(f"📥 Downloading from {link_type}: {download_url}")
            
            headers = {
                'User-Agent': 'QuantumAI/1.0 (Universal Explorer)'
            }
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=60)
            
            if response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Download failed with status {response.status_code}",
                    "link_type": link_type
                }
            
            # Determine filename
            if not filename:
                # Try to get from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    # Use last part of URL or default
                    filename = os.path.basename(urlparse(url).path) or 'downloaded_file'
            
            # Save file
            file_path = os.path.join(self.download_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path)
            
            return {
                "status": "success",
                "filename": filename,
                "path": file_path,
                "size": file_size,
                "link_type": link_type,
                "message": f"File downloaded successfully from {link_type}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "link_type": link_type if 'link_type' in locals() else 'unknown'
            }
    
    def get_instructions(self, link_type: str) -> str:
        """Get instructions for sharing files from different services"""
        
        instructions = {
            'google_drive': """
            📎 Google Drive:
            1. Right-click file → Share → Get link
            2. Set to "Anyone with the link"
            3. Copy link (looks like: drive.google.com/file/d/...)
            4. Paste here
            """,
            'dropbox': """
            📎 Dropbox:
            1. Right-click file → Share → Create link
            2. Copy link (looks like: dropbox.com/s/...)
            3. Paste here
            """,
            'onedrive': """
            📎 OneDrive:
            1. Right-click file → Share → Copy link
            2. Make sure "Anyone with the link can view"
            3. Copy link (looks like: onedrive.live.com/...)
            4. Paste here
            """
        }
        
        return instructions.get(link_type, "Paste a shareable link from cloud storage")


# Singleton
_shared_link_handler = None

def get_shared_link_handler():
    """Get or create shared link handler instance"""
    global _shared_link_handler
    
    if _shared_link_handler is None:
        _shared_link_handler = SharedLinkHandler()
    
    return _shared_link_handler
