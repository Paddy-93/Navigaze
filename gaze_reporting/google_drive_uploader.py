#!/usr/bin/env python3
"""
Google Drive Uploader for Navigaze Test Results

This script compresses and uploads gaze test session folders to Google Drive
with organized folder structure by date.

Usage:
    python google_drive_uploader.py /path/to/gaze_test_session_20250930_112742

Requirements:
    - credentials.json file in the same directory
    - google-api-python-client, google-auth-httplib2, google-auth-oauthlib packages
"""

import os
import sys
import json
import zipfile
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"[ERROR] Missing required packages: {e}")
    print("Please install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Configuration
DRIVE_FOLDER_NAME = "Navigaze Test Results"
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


class GoogleDriveUploader:
    def __init__(self):
        self.service = None
        self.root_folder_id = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        print("🔐 Authenticating with Google Drive...")
        
        creds = None
        
        # Load existing token if available
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            except Exception as e:
                print(f"[WARN] Error loading existing token: {e}")
                os.remove(TOKEN_FILE)  # Remove invalid token
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"[WARN] Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"[ERROR] {CREDENTIALS_FILE} not found!")
                    print("Please download your credentials.json from Google Cloud Console")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"[ERROR] Authentication failed: {e}")
                    return False
            
            # Save credentials for next time
            try:
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[WARN] Warning: Could not save token: {e}")
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            print("[OK] Successfully authenticated with Google Drive")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to build Drive service: {e}")
            return False
    
    def get_or_create_root_folder(self) -> Optional[str]:
        """Get or create the main Navigaze Test Results folder"""
        print(f"[INFO] Looking for '{DRIVE_FOLDER_NAME}' folder...")
        
        try:
            # Search for existing folder
            results = self.service.files().list(
                q=f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                print(f"[OK] Found existing folder: {DRIVE_FOLDER_NAME}")
                return folder_id
            else:
                # Create new folder
                print(f"[INFO] Creating new folder: {DRIVE_FOLDER_NAME}")
                folder_metadata = {
                    'name': DRIVE_FOLDER_NAME,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                print(f"[OK] Created folder: {DRIVE_FOLDER_NAME}")
                return folder_id
                
        except HttpError as e:
            print(f"[ERROR] Error accessing Google Drive: {e}")
            return None
    
    def get_or_create_date_folder(self, date_str: str) -> Optional[str]:
        """Get or create a date-specific folder (e.g., 2025-01-30)"""
        print(f"[INFO] Looking for date folder: {date_str}")
        
        try:
            # Search for existing date folder
            results = self.service.files().list(
                q=f"name='{date_str}' and mimeType='application/vnd.google-apps.folder' and parents in '{self.root_folder_id}' and trashed=false",
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                print(f"[OK] Found existing date folder: {date_str}")
                return folder_id
            else:
                # Create new date folder
                print(f"[INFO] Creating date folder: {date_str}")
                folder_metadata = {
                    'name': date_str,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.root_folder_id]
                }
                
                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                print(f"[OK] Created date folder: {date_str}")
                return folder_id
                
        except HttpError as e:
            print(f"[ERROR] Error creating date folder: {e}")
            return None
    
    def check_file_exists(self, filename: str, parent_folder_id: str) -> bool:
        """Check if a file already exists in the folder"""
        try:
            results = self.service.files().list(
                q=f"name='{filename}' and parents in '{parent_folder_id}' and trashed=false",
                fields="files(id, name)"
            ).execute()
            
            return len(results.get('files', [])) > 0
        except HttpError:
            return False
    
    def compress_session_folder(self, session_path: str) -> Optional[str]:
        """Compress the session folder to a ZIP file"""
        session_path = Path(session_path)
        
        if not session_path.exists():
            print(f"[ERROR] Session folder not found: {session_path}")
            return None
        
        if not session_path.is_dir():
            print(f"[ERROR] Path is not a directory: {session_path}")
            return None
        
        # Create ZIP filename
        zip_filename = f"{session_path.name}.zip"
        zip_path = session_path.parent / zip_filename
        
        print(f"[INFO] Compressing {session_path.name}...")
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(session_path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(session_path.parent)
                        zipf.write(file_path, arcname)
            
            zip_size = zip_path.stat().st_size
            print(f"[OK] Compressed to {zip_filename} ({zip_size / (1024*1024):.1f} MB)")
            return str(zip_path)
            
        except Exception as e:
            print(f"[ERROR] Error compressing folder: {e}")
            return None
    
    def upload_file(self, file_path: str, filename: str, parent_folder_id: str) -> Optional[str]:
        """Upload a file to Google Drive"""
        print(f"[UPLOAD] Uploading {filename}...")
        
        try:
            # Check if file already exists
            if self.check_file_exists(filename, parent_folder_id):
                print(f"[WARN] File already exists: {filename}")
                response = input("Do you want to overwrite it? (y/N): ").strip().lower()
                if response != 'y':
                    print("[ERROR] Upload cancelled")
                    return None
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            
            # Upload file with progress tracking
            media = MediaFileUpload(file_path, resumable=True)
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            # Track upload progress
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"\r📤 Uploading... {progress}%", end='', flush=True)
            
            print(f"\n[OK] Upload completed: {filename}")
            return response.get('id')
            
        except HttpError as e:
            print(f"\n[ERROR] Upload failed: {e}")
            return None
        except Exception as e:
            print(f"\n[ERROR] Upload error: {e}")
            return None
    
    def get_shareable_link(self, file_id: str) -> str:
        """Get a shareable link for the uploaded file"""
        try:
            # Make file publicly viewable
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            # Get file info
            file_info = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file_info.get('webViewLink', '')
            
        except Exception as e:
            print(f"[WARN] Could not create shareable link: {e}")
            return ""
    
    def upload_session(self, session_path: str, cleanup: bool = True) -> bool:
        """Main method to upload a session folder"""
        print("[START] Starting Google Drive upload process...")
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Get root folder
        self.root_folder_id = self.get_or_create_root_folder()
        if not self.root_folder_id:
            return False
        
        # Get current date for folder organization
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_folder_id = self.get_or_create_date_folder(date_str)
        if not date_folder_id:
            return False
        
        # Compress session folder
        zip_path = self.compress_session_folder(session_path)
        if not zip_path:
            return False
        
        # Upload compressed file with unique timestamp
        base_filename = Path(zip_path).stem
        timestamp_suffix = datetime.now().strftime("_%H%M%S_%f")[:-3]  # Add milliseconds
        zip_filename = f"{base_filename}{timestamp_suffix}.zip"
        file_id = self.upload_file(zip_path, zip_filename, date_folder_id)
        if not file_id:
            return False
        
        # Get shareable link
        shareable_link = self.get_shareable_link(file_id)
        
        # Clean up local ZIP file if requested
        if cleanup:
            try:
                os.remove(zip_path)
                print(f"[CLEANUP] Cleaned up local file: {zip_filename}")
            except Exception as e:
                print(f"[WARN] Could not clean up local file: {e}")
        
        # Print success message
        print("\n" + "="*60)
        print("[SUCCESS] UPLOAD SUCCESSFUL!")
        print("="*60)
        print(f"[INFO] Folder: {DRIVE_FOLDER_NAME}/{date_str}")
        print(f"📄 File: {zip_filename}")
        if shareable_link:
            print(f"🔗 Shareable link: {shareable_link}")
        print("="*60)
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Upload Navigaze test results to Google Drive')
    parser.add_argument('session_path', help='Path to the gaze test session folder')
    parser.add_argument('--keep-zip', action='store_true', help='Keep the local ZIP file after upload')
    
    args = parser.parse_args()
    
    # Validate session path
    session_path = Path(args.session_path)
    if not session_path.exists():
        print(f"[ERROR] Session folder not found: {session_path}")
        sys.exit(1)
    
    if not session_path.is_dir():
        print(f"[ERROR] Path is not a directory: {session_path}")
        sys.exit(1)
    
    # Create uploader and upload
    uploader = GoogleDriveUploader()
    success = uploader.upload_session(str(session_path), cleanup=not args.keep_zip)
    
    if success:
        print("\n[OK] Upload completed successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
