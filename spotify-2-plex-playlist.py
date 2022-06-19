import os
import re
import logging
from typing import List
from plexapi.server import PlexServer
from plexapi.audio import Track
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
load_dotenv()
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIFY_LIST = os.environ.get("SPOTIFY_LIST")
PLEX_TOKEN = os.environ.get("PLEX_TOKEN")
PLEX_BASE_URL = os.environ.get("PLEX_BASE_URL")

def filterPlexArray(plexItems=[], song="", artist="") -> List[Track]:
    for item in list(plexItems):
        if type(item) is not Track:
            plexItems.remove(item)
            continue
        if item.title.lower() != song.lower():
            plexItems.remove(item)
            continue
        artistItem = item.artist()
        if artistItem.title.lower() != artist.lower():
            plexItems.remove(item)
            continue

    return plexItems


def getSpotifyPlaylist(sp: spotipy.client, userId: str, playlistId: str) -> []:
    playlist = sp.user_playlist(userId, playlistId)
    return playlist


# Returns a list of spotify playlist objects
def getSpotifyUserPlaylists(sp: spotipy.client, userId: str) -> []:
    playlists = sp.user_playlists(userId)
    spotifyPlaylists = []
    while playlists:
        playlistItems = playlists['items']
        for i, playlist in enumerate(playlistItems):
            if playlist['owner']['id'] == userId:
                spotifyPlaylists.append(getSpotifyPlaylist(sp, userId, playlist['id']))
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return spotifyPlaylists


def getSpotifyTracks(sp: spotipy.client, playlist: []) -> []:
    spotifyTracks = []
    tracks = playlist['tracks']
    spotifyTracks.extend(tracks['items'])
    while tracks['next']:
        tracks = sp.next(tracks)
        spotifyTracks.extend(tracks['items'])
    return spotifyTracks


def getPlexTracks(plex: PlexServer, spotifyTracks: []) -> List[Track]:
    plexTracks = []
    for spotifyTrack in spotifyTracks:
        track = spotifyTrack['track']
        logging.info(f"Searching Plex for: {track['name']} by {track['artists'][0]['name']}")

        try:
            musicTracks = plex.search(track['name'], mediatype='track')
        except:
            try:
                musicTracks = plex.search(track['name'], mediatype='track')
            except:
                logging.info("Issue making plex request")
                continue

        if len(musicTracks) > 0:
            plexMusic = filterPlexArray(musicTracks, track['name'], track['artists'][0]['name'])
            if len(plexMusic) > 0:
                logging.info(f"Found Plex Song: {track['name']} by {track['artists'][0]['name']}")
                plexTracks.append(plexMusic[0])
            else:
                logging.info(f"Could not find song on Plex: {track['name']} by {track['artists'][0]['name']}")
    return plexTracks


def createPlaylist(plex: PlexServer, sp: spotipy.Spotify, playlist: []):
    playlistName = playlist['name']
    logging.info(f'Starting playlist {playlistName}')
    plexTracks = getPlexTracks(plex, getSpotifyTracks(sp, playlist))
    if len(plexTracks) > 0:
        try:
            plexPlaylist = plex.playlist(playlistName)
            logging.info(f'Updating playlist {playlistName}')
            plexPlaylist.addItems(plexTracks)
        except:
            logging.info(f"Creating playlist {playlistName}")
            plex.createPlaylist(playlistName, items=plexTracks)

def parseSpotifyURI(uriString: str) -> {}:
    spotifyUriStrings = re.sub(r'^spotify:', '', uriString).split(":")
    spotifyUriParts = {}
    for i, string in enumerate(spotifyUriStrings):
        if i % 2 == 0:
            spotifyUriParts[spotifyUriStrings[i]] = spotifyUriStrings[i+1]

    return spotifyUriParts


def runSync(plex : PlexServer, sp : spotipy.Spotify, spotifyURIs: []):
    logging.info('Starting a Sync Operation')
    playlists = []

    for spotifyUriParts in spotifyURIs:
        if 'user' in spotifyUriParts.keys() and 'playlist' not in spotifyUriParts.keys():
            logging.info(f"Getting playlists for {spotifyUriParts['user']}")
            playlists.extend(getSpotifyUserPlaylists(sp, spotifyUriParts['user']))
        elif 'user' in spotifyUriParts.keys() and 'playlist' in spotifyUriParts.keys():
            logging.info(f"Getting playlist {spotifyUriParts['user']} from user {spotifyUriParts['playlist']}")
            playlists.append(getSpotifyPlaylist(sp, spotifyUriParts['user'], spotifyUriParts['playlist']))

    for playlist in playlists:
        createPlaylist(plex, sp, playlist)
    logging.info('Finished a Sync Operation')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    spotifyUris = SPOTIFY_LIST
    if spotifyUris is None:
        logging.error("No spotify uris")

    plex = PlexServer(PLEX_BASE_URL, PLEX_TOKEN)

    client_credentials_manager = SpotifyClientCredentials()
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    spotifyUris = spotifyUris.split(",")

    spotifyMainUris = []

    for spotifyUri in spotifyUris:
        spotifyUriParts = parseSpotifyURI(spotifyUri)
        spotifyMainUris.append(spotifyUriParts)

    runSync(plex, sp, spotifyMainUris)
