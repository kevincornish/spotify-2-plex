# spotify-2-plex

Move spotify playlists over to plex

## Installation

Create new python env

```bash
python -m venv env
```

activate env

```bash
source env/bin/activate
```

install requirements

```bash
pip install -r requirements.txt
```

## Setup .env

Rename .env.example to .env

`SPOTIPY_CLIENT_ID` - Create: https://developer.spotify.com/dashboard/login

`SPOTIPY_CLIENT_SECRET` - Client secret from created client id

`PLEX_URL` - Plex url: `http://plex:32400`

`PLEX_TOKEN` - Plex token https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/

`SPOTIFY_URIS` - A comma seperated list of the spotify URI's to import: `spotify:user:kevz,spotify:user:kevz:playlist:abcd123`

- User's URI imports all public playlists: `spotify:user:kevz`
- Playlist URI imports a specific playlist (must be public): `spotify:user:kevz:playlist:12345abc`
