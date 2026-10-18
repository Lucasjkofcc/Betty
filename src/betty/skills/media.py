import subprocess as sp
import sys
if sys.platform.startswith("win"):
    from libspotifyctl import SpotifyClient
    def proxima_media():
        with SpotifyClient() as spotify:
            spotify.next()
    def anterior_media():
        with SpotifyClient() as spotify:
            spotify.previous()
    def pausar_temporario():
        with SpotifyClient() as spotify:
            spotify.pause()
    def retomar_temporario():
        with SpotifyClient() as spotify:
            spotify.play()
if sys.platform.startswith("linux"):
    def pausar_temporario():
        sp.Popen(["playerctl", "pause"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)
    def retomar_temporario():
        sp.Popen(["playerctl", "play"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)


    def proxima_media():
        sp.Popen(["playerctl", "next"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)


    def anterior_media():
        sp.Popen(["playerctl", "previous"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)
