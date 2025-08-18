import requests
import base64

def get_song_danceability(song_name, artist_name, client_id, client_secret):
    # Get access token
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    response = requests.post(auth_url, headers=headers, data=data)
    access_token = response.json()["access_token"]
    
    # Search for the track
    search_url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    params = {
        "q": f"track:{song_name} artist:{artist_name}",
        "type": "track",
        "limit": 1
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    track_id = response.json()["tracks"]["items"][0]["id"]
    
    # Get audio features
    audio_features_url = f"https://api.spotify.com/v1/audio-features/{track_id}"
    response = requests.get(audio_features_url, headers=headers)
    audio_features = response.json()
    
    return audio_features["danceability"]

# Usage
if __name__=="__main__":
    danceability = get_song_danceability("Blinding Lights", "The Weeknd", "ef74230f33aa4a0b82d54230a5d72ba9", "c857bf3d47774c9698b1492544fa5f5c")
    print(f"Danceability: {danceability}")  # Returns a value between 0.0 and 1.0