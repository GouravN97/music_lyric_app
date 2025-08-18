import requests
import os
import base64
import re
from pathlib import Path
import wikipedia
import time
import wikipedia_trial

class MusicImageDownloader:
    def __init__(self, spotify_client_id, spotify_client_secret, lastfm_api_key):
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.lastfm_api_key = lastfm_api_key
        self.spotify_token = None
        self.token_expires = 0
    
    def _clean_name(self, name):
        """Convert to lowercase, remove spaces and special chars"""
        return re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
    
    def _get_spotify_token(self):
        """Get Spotify token with expiration handling"""
        current_time = time.time()
        
        if self.spotify_token and current_time < self.token_expires:
            return self.spotify_token
        
        auth = base64.b64encode(f"{self.spotify_client_id}:{self.spotify_client_secret}".encode()).decode()
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"}
        )
        
        token_data = response.json()
        self.spotify_token = token_data["access_token"]
        self.token_expires = current_time + token_data.get("expires_in", 3600) - 60
        return self.spotify_token
    
    def _get_largest_image(self, images):
        """Get the largest image from a list of Spotify images"""
        if not images:
            return None
        
        # Sort by total pixels (width * height), then by width
        largest = max(images, key=lambda img: (img.get('width', 0) * img.get('height', 0), img.get('width', 0)))
        return largest
    
    def _download_image(self, url, filepath, source):
        """Download image with proper headers"""
        headers = {
            'User-Agent': 'MusicDownloader/1.0 (contact@example.com)',
        }
        if 'wikimedia.org' in url:
            headers['User-Agent'] = 'MusicDownloader/1.0 (Personal project; contact@example.com) Python/requests'
            headers['Referer'] = 'https://en.wikipedia.org/'
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            
            print(f"✓ {source}: {filepath.name}")
            return True
        except Exception as e:
            print(f"✗ {source}: {e}")
            return False
    
    def get_spotify_images(self, artist, song, folder):
        """Get comprehensive images from Spotify - largest versions only"""
        token = self._get_spotify_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"🎵 Searching Spotify for: {song} by {artist}")
        
        # Search for track
        track_response = requests.get(
            "https://api.spotify.com/v1/search",
            headers=headers,
            params={"q": f"track:{song} artist:{artist}", "type": "track", "limit": 1}
        )
        
        tracks = track_response.json().get("tracks", {}).get("items", [])
        if not tracks:
            print("✗ Spotify: Track not found")
            return
        
        track = tracks[0]
        artist_id = track["artists"][0]["id"]
        album_id = track["album"]["id"]
        
        print(f"   Found track: {track['name']} from album: {track['album']['name']}")
        artist_response = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
        artist_data = artist_response.json()
        '''
        # 1. Download the specific album cover (largest version)
        album_images = track["album"]["images"]
        if album_images:
            largest_album = self._get_largest_image(album_images)
            if largest_album:
                size = f"{largest_album['width']}x{largest_album['height']}"
                filename = f"spotify_album_{track['album']['name'].replace(' ', '_')}_{size}.jpg"
                filename = re.sub(r'[^a-zA-Z0-9._]', '', filename)
                self._download_image(largest_album["url"], folder / filename, "Spotify Album")
        
        # 2. Download artist image (largest version)
        artist_response = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
        
        
        if artist_data.get("images"):
            largest_artist = self._get_largest_image(artist_data["images"])
            if largest_artist:
                size = f"{largest_artist['width']}x{largest_artist['height']}"
                filename = f"spotify_artist_{artist_data['name'].replace(' ', '_')}_{size}.jpg"
                filename = re.sub(r'[^a-zA-Z0-9._]', '', filename)
                self._download_image(largest_artist["url"], folder / filename, "Spotify Artist")
        '''
        # 3. Get ALL albums by this artist and download their covers
        print(f"   Getting all albums by {artist_data.get('name', artist)}")
        
        albums_response = requests.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/albums",
            headers=headers,
            params={
                "include_groups": "album,single,compilation",
                "market": "US",
                "limit": 15  # Get up to 15 albums
            }
        )
        
        albums_data = albums_response.json()
        albums = albums_data.get("items", [])
        
        print(f"   Found {len(albums)} albums/singles")
        
        downloaded_albums = set()  # Track to avoid duplicates
        
        for album in albums:
            # Skip if we already downloaded this album
            album_name = album.get("name", "")
            if album_name in downloaded_albums:
                continue
            
            album_images = album.get("images", [])
            if album_images:
                largest_img = self._get_largest_image(album_images)
                if largest_img:
                    size = f"{largest_img['width']}x{largest_img['height']}"
                    safe_album_name = re.sub(r'[^a-zA-Z0-9]', '', album_name.replace(' ', '_'))
                    filename = f"spotify_album_{safe_album_name}_{size}.jpg"
                    
                    if self._download_image(largest_img["url"], folder/filename, f"Spotify Album ({album_name})"):
                        downloaded_albums.add(album_name)
            
            time.sleep(0.1)  # Small delay to be respectful
        
        
    def download_all(self, artist_name, song_name):
        """Download images from all sources"""
        # Create folder name
        folder_name = f"{self._clean_name(song_name)}_{self._clean_name(artist_name)}"
        folder = Path(folder_name)
        folder.mkdir(exist_ok=True)
        
        print(f"📁 Downloading to: {folder_name}/")
        print(f"🎵 Artist: {artist_name}")
        print(f"🎶 Song: {song_name}")
        print("-" * 50)
        
        # Download from all sources
        self.get_spotify_images(artist_name, song_name, folder)
        #self.get_wikipedia_images(artist_name, song_name, folder)
        
        # Summary
        downloaded_files = list(folder.glob("*.jpg"))
        print(f"\n✅ Downloaded {len(downloaded_files)} images to {folder_name}/")
        
        # Show breakdown
        spotify_files = [f for f in downloaded_files if 'spotify' in f.name]
        #wikipedia_files = [f for f in downloaded_files if 'wikipedia' in f.name]
        
        print(f"   📊 Breakdown:")
        print(f"   - Spotify: {len(spotify_files)} images")
        #print(f"   - Wikipedia: {len(wikipedia_files)} images")


def main(title, artist,album,file_path):
    # Configuration - Replace with your API keys
    SPOTIFY_CLIENT_ID = "ef74230f33aa4a0b82d54230a5d72ba9"
    SPOTIFY_CLIENT_SECRET = "c857bf3d47774c9698b1492544fa5f5c"
    LASTFM_API_KEY = "35acfbd239b707f08c0a1a5915586f55"
    
    downloader = MusicImageDownloader(
        SPOTIFY_CLIENT_ID, 
        SPOTIFY_CLIENT_SECRET, 
        LASTFM_API_KEY
    )
    
    # Multiple downloads
    tracks = [
        (artist,title)
    ]
    
    for artist, song in tracks:
        print("\n" + "="*60)
        downloader.download_all(artist, song)
    wikipedia_trial.main(artist,album,file_path)

if __name__ == "__main__":
    main("The Strokes","Reptilia")
    