import requests
import re
import time
from pathlib import Path
from urllib.parse import urlparse, unquote
import json

class WikipediaImageDownloader:
    def __init__(self, contact_email="your-email@example.com"):
        self.contact_email = contact_email
        self.session = requests.Session()
        
        # Proper User-Agent that complies with Wikimedia policy
        self.session.headers.update({
            'User-Agent': f'MusicWikipediaDownloader/1.0 (Personal music image downloader; {contact_email})',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.api_base = "https://en.wikipedia.org/w/api.php"
    
    def _clean_name(self, name):
        """Convert to lowercase, remove spaces and special chars"""
        return re.sub(r'[^a-z0-9]', '', name.lower().replace(' ', ''))
    
    def _safe_filename(self, url, prefix="image"):
        """Create safe filename from URL"""
        parsed = urlparse(url)
        filename = unquote(parsed.path.split('/')[-1])
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Ensure it has an extension
        if '.' not in filename or len(filename.split('.')[-1]) > 4:
            filename += '.jpg'
        
        return f"{prefix}_{filename}"
    
    def _download_image(self, url, filepath):
        """Download image with proper headers and error handling"""
        try:
            # Add specific headers for image downloads
            headers = self.session.headers.copy()
            headers.update({
                'Referer': 'https://en.wikipedia.org/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
            })
            
            response = self.session.get(url, headers=headers, stream=True, timeout=20)
            response.raise_for_status()
            
            # Check if it's actually an image
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"⚠ Skipping non-image: {url} (Type: {content_type})")
                return False
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file size
            if filepath.stat().st_size == 0:
                filepath.unlink()
                print(f"✗ Empty file downloaded: {url}")
                return False
            
            print(f"✓ Downloaded: {filepath.name} ({filepath.stat().st_size:,} bytes)")
            return True
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"✗ Access forbidden (403): {url}")
                print("  This image may be restricted or have licensing issues")
            elif e.response.status_code == 404:
                print(f"✗ Image not found (404): {url}")
            else:
                print(f"✗ HTTP {e.response.status_code}: {url}")
            return False
        except Exception as e:
            print(f"✗ Download failed: {url} - {str(e)}")
            return False
    
    def search_pages(self, query, limit=5):
        """Search for Wikipedia pages"""
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': query,
            'srlimit': limit,
            'srprop': 'title|snippet'
        }
        
        try:
            response = self.session.get(self.api_base, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'query' in data and 'search' in data['query']:
                return [(page['title'], page.get('snippet', '')) for page in data['query']['search']]
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_page_images(self, page_title, limit=10):
        """Get images from a Wikipedia page using API"""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': page_title,
            'prop': 'images',
            'imlimit': limit
        }
        
        try:
            response = self.session.get(self.api_base, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'images' in page_data:
                    return [img['title'] for img in page_data['images']]
            return []
        except Exception as e:
            print(f"Page images error: {e}")
            return []
    
    def get_image_urls(self, image_titles):
        """Get actual URLs for image files"""
        if not image_titles:
            return []
        
        # Filter for actual image files
        image_titles = [title for title in image_titles 
                       if any(ext in title.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
        
        if not image_titles:
            return []
        
        # Batch request for image info
        titles_param = '|'.join(image_titles[:10])  # Limit to 10 to avoid URL too long
        
        params = {
            'action': 'query',
            'format': 'json',
            'titles': titles_param,
            'prop': 'imageinfo',
            'iiprop': 'url|size|mime',
            'iiurlwidth': 800  # Get reasonable size
        }
        
        try:
            response = self.session.get(self.api_base, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            image_urls = []
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if 'imageinfo' in page_data and page_data['imageinfo']:
                    info = page_data['imageinfo'][0]
                    image_urls.append({
                        'title': page_data.get('title', ''),
                        'url': info.get('url', ''),
                        'thumb_url': info.get('thumburl', info.get('url', '')),
                        'width': info.get('width', 0),
                        'height': info.get('height', 0),
                        'size': info.get('size', 0)
                    })
            
            return image_urls
        except Exception as e:
            print(f"Image URL error: {e}")
            return []
    
    def download_artist_images(self, artist_name, folder, max_images=15):
        """Download artist images from Wikipedia"""
        print(f"🎤 Searching for artist: {artist_name}")
        
        # Search strategies
        search_queries = [
            artist_name,
            f"{artist_name} musician",
            f"{artist_name} singer",
            f"{artist_name} band"
        ]
        
        downloaded_count = 0
        
        for query in search_queries:
            if downloaded_count >= max_images:
                break
                
            print(f"   Searching: {query}")
            pages = self.search_pages(query, limit=6)
            
            for page_title, snippet in pages:
                if downloaded_count >= max_images:
                    break
                    
                print(f"   Checking page: {page_title}")
                
                # Get images from this page
                image_titles = self.get_page_images(page_title, limit=8)
                if not image_titles:
                    continue
                
                # Get actual image URLs
                image_urls = self.get_image_urls(image_titles)
                
                for img_data in image_urls:
                    if downloaded_count >= max_images:
                        break
                    
                    url = img_data.get('thumb_url') or img_data.get('url')
                    if not url:
                        continue
                    
                    # Skip obviously irrelevant images
                    title_lower = img_data.get('title', '').lower()
                    if any(skip in title_lower for skip in ['commons-logo', 'edit-icon', 'ambox', 'wikimedia']):
                        continue
                    
                    artist_list = artist_name.split()
                    artist_list = [x for x in artist_list if x.lower() != 'the']
                    if all(keyword.lower() not in title_lower for keyword in artist_list):
                        continue
                    
                    filename = self._safe_filename(url, f"artist_{downloaded_count+1}")
                    filepath = folder / filename
                    
                    if self._download_image(url, filepath):
                        downloaded_count += 1
                        time.sleep(1)  # Be respectful to servers
                
                time.sleep(0.5)  # Small delay between pages
        
        return downloaded_count
    
    def download_album_images(self, album_name, artist_name, folder, max_images=3):
        """Download album images from Wikipedia"""
        print(f"💿 Searching for album: {album_name} by {artist_name}")
        
        # Search strategies for albums
        search_queries = [
            f"{album_name} {artist_name} album",
            f"{album_name} album {artist_name}",
            f'"{album_name}" {artist_name}',
        ]
        
        downloaded_count = 0
        
        for query in search_queries:
            if downloaded_count >= max_images:
                break
                
            print(f"   Searching: {query}")
            pages = self.search_pages(query, limit=10)
            
            for page_title, snippet in pages:
                if downloaded_count >= max_images:
                    break
                    
                # Skip if this doesn't seem album-related
                if not any(word in page_title.lower() for word in ['album', album_name.lower()]):
                    continue
                
                print(f"   Checking page: {page_title}")
                
                image_titles = self.get_page_images(page_title, limit=15)
                if not image_titles:
                    continue
                
                image_urls = self.get_image_urls(image_titles)
                
                for img_data in image_urls:
                    if downloaded_count >= max_images:
                        break
                    
                    url = img_data.get('thumb_url') or img_data.get('url')
                    if not url:
                        continue
                    
                    # Prefer larger images for albums (likely cover art)
                    if img_data.get('width', 0) < 200:
                        continue
                    
                    filename = self._safe_filename(url, f"album_{downloaded_count+1}")
                    checklist = album_name.split()
                    checklist = [x for x in checklist if x.lower() != 'the']
                    if all(keyword.lower() not in filename.lower() for keyword in checklist):
                        continue
                    filepath = folder / filename
                    
                    if self._download_image(url, filepath):
                        downloaded_count += 1
                        time.sleep(1)
                
                time.sleep(0.5)
        
        return downloaded_count
    
    def download_all(self, artist_name, album_name, file_path):
        """Download images for artist and optionally album to specified folder"""
        # Convert file_path to Path object and ensure it exists
        folder = Path(file_path)
        folder.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist
        
        print(f"📁 Downloading to: {folder.absolute()}/")
        print(f"🎵 Artist: {artist_name}")
        if album_name:
            print(f"💿 Album: {album_name}")
        print("-" * 60)
        
        # Download artist images
        artist_count = self.download_artist_images(artist_name, folder, max_images=8)
        
        # Download album images if specified
        album_count = 0
        #if album_name:
        #    album_count = self.download_album_images(album_name, artist_name, folder, max_images=8)
        
        # Summary
        total_images = list(folder.glob("*.jpg")) + list(folder.glob("*.png")) + list(folder.glob("*.gif")) + list(folder.glob("*.webp"))
        print(f"\n✅ Successfully downloaded {len(total_images)} images")
        print(f"   Artist images: {artist_count}")
        if album_name:
            print(f"   Album images: {album_count}")
        print(f"   Saved to: {folder.absolute()}/")
        
        return len(total_images)


def main(artist, album, file_path):
    """Main function that downloads images to the specified folder path"""
    # Initialize downloader with your contact email
    downloader = WikipediaImageDownloader(contact_email="gouravn02@gmail.com")
    
    # Convert file_path to Path object for validation
    target_folder = Path(file_path)
    
    print(f"🎯 Target folder: {target_folder.absolute()}")
    print(f"📂 Folder exists: {target_folder.exists()}")
    
    # Create folder if it doesn't exist
    if not target_folder.exists():
        print(f"📁 Creating folder: {target_folder}")
        target_folder.mkdir(parents=True, exist_ok=True)
    
    # Download images
    downloader.download_all(artist, album, file_path)


# Example usage functions
def download_to_existing_folder():
    """Example: Download to an existing folder"""
    # Specify your existing folder path
    existing_folder = "thislove_maroon5"  # or "C:/Users/username/Music/Images" on Windows
    
    # Download images for artist and album
    main("Maroon 5", "Songs about Jane", existing_folder)


def download_multiple_to_same_folder():
    """Example: Download multiple artists to the same folder"""
    shared_folder = "shared_music_collection"
    
    artists_albums = [
        ("The Beatles", "Abbey Road"),
        ("Drake", "Scorpion"),
        ("Billie Eilish", None),  # Artist only, no album
    ]
    
    for artist, album in artists_albums:
        print(f"\n{'='*80}")
        main(artist, album, shared_folder)


if __name__ == "__main__":
    # Example 1: Download to a specific existing folder
    download_to_existing_folder()
    
    print(f"\n{'='*100}")
    
    # Example 2: Download multiple artists to same folder
    #download_multiple_to_same_folder()