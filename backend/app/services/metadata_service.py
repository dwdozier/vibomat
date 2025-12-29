from backend.core.metadata import MetadataVerifier


class MetadataService:
    def __init__(self):
        self.verifier = MetadataVerifier()

    def verify_track(self, artist: str, track: str, version: str = "studio") -> bool:
        return self.verifier.verify_track_version(artist, track, version)
