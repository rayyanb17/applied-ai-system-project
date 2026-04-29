"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs

NEW: Use the AI-powered playlist generator to create playlists for any activity.
"""

try:
    from .recommender import load_songs, recommend_songs, retrieve_songs_for_task, build_study_playlist
    from .task_parser import parse_activity_request, activity_to_music_profile, clarify_user_preferences
except ImportError:
    from recommender import load_songs, recommend_songs, retrieve_songs_for_task, build_study_playlist
    from task_parser import parse_activity_request, activity_to_music_profile, clarify_user_preferences


def main_original_recommender() -> None:
    """Original music recommender mode (demo with hardcoded profiles)."""
    print("\n" + "="*60)
    print("MODE: Original Music Recommender")
    print("="*60 + "\n") 

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


def main_playlist_generator() -> None:
    """AI-powered playlist generator for any activity."""
    print("\n" + "="*60)
    print("MODE: AI Playlist Generator")
    print("="*60)
    print("\nDescribe what you need music for:")
    print("  Examples: 'I need music for a 90 minute workout'")
    print("           'give me a 2-hour road trip playlist'")
    print("           'I want a lot of rap songs for a race'")
    print("           'music for my cross country trip'")
    print("           'I need chill music for studying'\n")
    
    user_request = input("Your request: ").strip()
    
    if not user_request:
        print("No request provided. Using default 60-minute balanced playlist.")
        user_request = "60 minute general playlist"
    
    print(f"\nProcessing: '{user_request}'")
    
    # Parse activity request using Gemini or fallback
    activity_info = parse_activity_request(user_request)
    
    # Check if parsing failed due to vague input
    if activity_info.get("error"):
        print(f"\n⚠️  {activity_info['message']}")
        print("\nPlease try again with a more descriptive request.\n")
        main_playlist_generator()  # Recursively prompt again
        return
    
    print(f"  Duration: {activity_info['duration_minutes']} minutes")
    print(f"  Activity: {activity_info['activity_type']}")
    print(f"  Vibe: {activity_info['vibe']}")
    print(f"  Energy level: {activity_info['energy_level']:.0%}")
    if activity_info.get('preferred_genres'):
        print(f"  Preferred genres: {', '.join(activity_info['preferred_genres'])}")
    if activity_info.get('preferred_artists_or_keywords'):
        print(f"  Keywords/Artists: {activity_info['preferred_artists_or_keywords']}")
    
    # Convert activity to music profile
    music_profile = activity_to_music_profile(activity_info)
    print(f"\nGenerated music profile:")
    print(f"  Genres: {', '.join(music_profile['preferred_genres'])}")
    print(f"  Moods: {', '.join(music_profile['preferred_moods'])}")
    print(f"  Energy: {music_profile['energy']:.0%}")
    print(f"  Acousticness: {music_profile['acousticness']:.0%}")
    
    # Load songs and retrieve candidates
    songs = load_songs("data/songs.csv")
    print(f"\nSearching catalog of {len(songs)} songs...")
    retrieved = retrieve_songs_for_task(music_profile, songs)
    
    # Validate and build playlist
    playlist, total_minutes, status = build_study_playlist(retrieved, activity_info['duration_minutes'])
    
    print(f"\n{status}\n")
    
    # Display playlist
    if playlist:
        print("=" * 60)
        print("YOUR PLAYLIST")
        print("=" * 60)
        for idx, song in enumerate(playlist, 1):
            print(f"{idx}. {song['title']} by {song['artist']}")
            print(f"   Genre: {song['genre']} | Mood: {song['mood']} | Energy: {song['energy']:.0%}")
            print()
        
        print(f"Total duration (estimated): ~{total_minutes:.0f} minutes")
    else:
        print("Could not build playlist. Try clarifying your preferences.")
        clarified = clarify_user_preferences()
        if clarified:
            print("Updated preferences. Try again with your next request.")


def main_menu() -> None:
    """Main menu for choosing between recommender modes."""
    print("\n" + "="*60)
    print("🎵 MUSIC RECOMMENDER & AI PLAYLIST GENERATOR")
    print("="*60)
    print("\nChoose a mode:")
    print("1. Original Music Recommender (demo profiles)")
    print("2. AI Playlist Generator (for any activity)")
    print("\nOr press Ctrl+C to exit.\n")
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        main_original_recommender()
    elif choice == "2":
        main_playlist_generator()
    else:
        print("Invalid choice. Please enter 1 or 2.")
        main_menu()


if __name__ == "__main__":
    # Interactive menu
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")

