"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from .recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    profiles = [
        (
            "Balanced baseline",
            {
                "genre": "pop",
                "mood": "happy",
                "energy": 0.8,
                "acousticness": 0.2,
                "valence": 0.8,
                "danceability": 0.8,
                "tempo": 0.65,
                "liked_artists": ["Neon Echo"],
                "seed_artist": "Neon Echo",
            },
        ),
        (
            "Conflict: aggressive but ambient",
            {
                "genre": "ambient",
                "mood": "aggressive",
                "energy": 0.95,
                "acousticness": 0.9,
                "tempo": 0.8,
            },
        ),
        (
            "Unknown categorical values",
            {
                "genre": "k-pop",
                "mood": "melancholy",
                "energy": 0.5,
                "valence": 0.45,
            },
        ),
        (
            "Out-of-range energy",
            {
                "genre": "lofi",
                "mood": "chill",
                "energy": 1.7,
                "acousticness": 0.95,
            },
        ),
        (
            "Artist-bias stress",
            {
                "genre": "jazz",
                "mood": "relaxed",
                "energy": 0.3,
                "liked_artists": ["Neon Echo", "Neon Echo", "Neon Echo"],
                "seed_artist": "Neon Echo",
            },
        ),
        (
            "Sparse numeric-only",
            {
                "energy": 0.35,
                "tempo": 0.15,
            },
        ),
    ]

    for label, user_prefs in profiles:
        recommendations = recommend_songs(user_prefs, songs, k=3)

        print(f"\nProfile: {label}")
        print("Top recommendations:\n")
        for rec in recommendations:
            # You decide the structure of each returned item.
            # A common pattern is: (song, score, explanation)
            song, score, explanation = rec
            print(f"{song['title']} - Score: {score:.2f}")
            print(f"Because: {explanation}")
            print()


if __name__ == "__main__":
    main()
