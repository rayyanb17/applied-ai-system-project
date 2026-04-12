from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
from pathlib import Path

# Weights sum to 1.0 and keep numeric features influential.
WEIGHTS = {
    "genre": 0.19,
    "mood": 0.14,
    "energy": 0.20,
    "acousticness": 0.15,
    "valence": 0.10,
    "danceability": 0.10,
    "tempo": 0.10,
    "same_artist": 0.02,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a numeric value to an inclusive range."""
    return max(low, min(high, value))


def _normalize_tempo(tempo_bpm: float, min_bpm: float, max_bpm: float) -> float:
    """Normalize BPM to a 0-1 range using catalog min and max values."""
    if max_bpm <= min_bpm:
        return 0.5
    return _clamp((tempo_bpm - min_bpm) / (max_bpm - min_bpm))


def _get_numeric_targets(user_prefs: Dict) -> Dict[str, float]:
    """Build numeric preference targets with sensible fallbacks."""
    return {
        "energy": float(user_prefs.get("energy", user_prefs.get("target_energy", 0.5))),
        "acousticness": float(
            user_prefs.get(
                "acousticness",
                user_prefs.get("target_acousticness", 1.0 if user_prefs.get("likes_acoustic", False) else 0.0),
            )
        ),
        "valence": float(user_prefs.get("valence", user_prefs.get("target_valence", 0.5))),
        "danceability": float(user_prefs.get("danceability", user_prefs.get("target_danceability", 0.5))),
        "tempo": float(user_prefs.get("tempo", user_prefs.get("target_tempo", 0.5))),
    }


def _active_components(user_prefs: Dict) -> List[str]:
    """Return score components that are explicitly present in user preferences."""
    active: List[str] = []

    if user_prefs.get("genre") is not None:
        active.append("genre")
    if user_prefs.get("mood") is not None:
        active.append("mood")

    if "energy" in user_prefs or "target_energy" in user_prefs:
        active.append("energy")
    if (
        "acousticness" in user_prefs
        or "target_acousticness" in user_prefs
        or "likes_acoustic" in user_prefs
    ):
        active.append("acousticness")
    if "valence" in user_prefs or "target_valence" in user_prefs:
        active.append("valence")
    if "danceability" in user_prefs or "target_danceability" in user_prefs:
        active.append("danceability")
    if "tempo" in user_prefs or "target_tempo" in user_prefs:
        active.append("tempo")
    if user_prefs.get("seed_artist") is not None or user_prefs.get("liked_artists"):
        active.append("same_artist")

    return active


def _score_song_dict(
    song: Dict,
    user_prefs: Dict,
    min_bpm: float,
    max_bpm: float,
) -> Tuple[float, Dict[str, float], List[str]]:
    """Compute a normalized weighted score and per-component match values."""
    targets = _get_numeric_targets(user_prefs)
    liked_artists = set(user_prefs.get("liked_artists", []))
    seed_artist = user_prefs.get("seed_artist")

    genre_match = 1.0 if song.get("genre") == user_prefs.get("genre") else 0.0
    mood_match = 1.0 if song.get("mood") == user_prefs.get("mood") else 0.0
    energy_close = 1.0 - abs(float(song.get("energy", 0.5)) - targets["energy"])
    acoustic_close = 1.0 - abs(float(song.get("acousticness", 0.5)) - targets["acousticness"])
    valence_close = 1.0 - abs(float(song.get("valence", 0.5)) - targets["valence"])
    danceability_close = 1.0 - abs(float(song.get("danceability", 0.5)) - targets["danceability"])

    normalized_song_tempo = _normalize_tempo(float(song.get("tempo_bpm", 0.0)), min_bpm, max_bpm)
    tempo_close = 1.0 - abs(normalized_song_tempo - _clamp(targets["tempo"]))

    same_artist = 0.0
    artist = song.get("artist")
    if artist and (artist in liked_artists or (seed_artist is not None and artist == seed_artist)):
        same_artist = 1.0

    components = {
        "genre": _clamp(genre_match),
        "mood": _clamp(mood_match),
        "energy": _clamp(energy_close),
        "acousticness": _clamp(acoustic_close),
        "valence": _clamp(valence_close),
        "danceability": _clamp(danceability_close),
        "tempo": _clamp(tempo_close),
        "same_artist": _clamp(same_artist),
    }

    active = _active_components(user_prefs)
    if not active:
        return 0.0, components, []

    weight_total = sum(WEIGHTS[name] for name in active)
    score = sum((WEIGHTS[name] / weight_total) * components[name] for name in active)
    return score, components, active


def _song_to_dict(song: "Song") -> Dict:
    """Convert a Song dataclass into the dictionary shape used by scorers."""
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "genre": song.genre,
        "mood": song.mood,
        "energy": song.energy,
        "tempo_bpm": song.tempo_bpm,
        "valence": song.valence,
        "danceability": song.danceability,
        "acousticness": song.acousticness,
    }


def _build_explanation(song: Dict, user_prefs: Dict, components: Dict[str, float], active: List[str]) -> str:
    """Generate a short explanation from the strongest active match signals."""
    reasons: List[str] = []
    if "genre" in active and components["genre"] == 1.0:
        reasons.append("genre match")
    if "mood" in active and components["mood"] == 1.0:
        reasons.append("mood match")
    if "same_artist" in active and components["same_artist"] == 1.0:
        reasons.append("same artist as your history")

    numeric_labels = {
        "energy": "energy",
        "acousticness": "acousticness",
        "valence": "valence",
        "danceability": "danceability",
        "tempo": "tempo",
    }
    available_numeric = [key for key in numeric_labels if key in active]
    best_numeric = sorted(available_numeric, key=lambda key: components[key], reverse=True)[:2]
    for key in best_numeric:
        reasons.append(f"similar {numeric_labels[key]}")

    if not reasons:
        return "Closest overall weighted fit to your profile."
    return "Matched on " + ", ".join(reasons) + "."

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        if not self.songs or k <= 0:
            return []

        min_bpm = min(song.tempo_bpm for song in self.songs)
        max_bpm = max(song.tempo_bpm for song in self.songs)
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }

        scored: List[Tuple[float, Song]] = []
        for song in self.songs:
            score, _, _ = _score_song_dict(_song_to_dict(song), user_prefs, min_bpm, max_bpm)
            scored.append((score, song))

        scored.sort(key=lambda item: (-item[0], item[1].id))
        return [song for _, song in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        if not self.songs:
            return "Closest overall weighted fit to your profile."

        min_bpm = min(candidate.tempo_bpm for candidate in self.songs)
        max_bpm = max(candidate.tempo_bpm for candidate in self.songs)
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        _, components, active = _score_song_dict(_song_to_dict(song), user_prefs, min_bpm, max_bpm)
        return _build_explanation(_song_to_dict(song), user_prefs, components, active)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []

    # Resolve relative paths from the project root when possible.
    path = Path(csv_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path

    with path.open(mode="r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            songs.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                }
            )

    print(f"Loaded songs: {len(songs)}")
    return songs

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    if not songs or k <= 0:
        return []

    min_bpm = min(float(song["tempo_bpm"]) for song in songs)
    max_bpm = max(float(song["tempo_bpm"]) for song in songs)

    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, components, active = _score_song_dict(song, user_prefs, min_bpm, max_bpm)
        explanation = _build_explanation(song, user_prefs, components, active)
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: (-item[1], int(item[0]["id"])))
    return scored[:k]
