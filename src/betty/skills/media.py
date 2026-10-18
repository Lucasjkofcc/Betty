import subprocess as sp
import sys
if sys.platform.startswith("win"):
    import threading

    from libspotifyctl import SpotifyClient

    def _run_spotify_action(action, start=False):
        def worker():
            with SpotifyClient() as spotify:
                if start:
                    spotify.start()
                getattr(spotify, action)()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def proxima_media():
        _run_spotify_action("next", start=True)

    def anterior_media():
        _run_spotify_action("previous")

    def pausar_temporario():
        _run_spotify_action("pause")

    def retomar_temporario():
        _run_spotify_action("play")
if sys.platform.startswith("linux"):
    def pausar_temporario():
        sp.Popen(["playerctl", "pause"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)
    def retomar_temporario():
        sp.Popen(["playerctl", "play"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)


    def proxima_media():
        sp.Popen(["playerctl", "next"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)


    def anterior_media():
        sp.Popen(["playerctl", "previous"],stderr=sp.DEVNULL, stdout=sp.DEVNULL)
