from src.recommender import Song, UserProfile, Recommender, retrieve_songs_for_task, build_study_playlist
from src.task_parser import parse_activity_request, activity_to_music_profile

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_parse_activity_request_extracts_duration():
    """Test that activity parser extracts duration correctly."""
    activity_info = parse_activity_request("90 minute workout")
    assert activity_info["duration_minutes"] == 90
    assert "workout" in activity_info["activity_type"].lower()


def test_parse_activity_request_rejects_vague_input():
    """Test that vague input gets flagged for clarification."""
    activity_info = parse_activity_request("just give me music")
    assert activity_info.get("error") is True
    assert "message" in activity_info


def test_activity_to_music_profile_generates_valid_profile():
    """Test that activity info converts to valid music profile."""
    activity_info = {
        "duration_minutes": 90,
        "activity_type": "workout",
        "preferred_genres": [],
        "preferred_artists_or_keywords": "",
        "energy_level": 0.8,
        "vibe": "energetic",
    }
    music_profile = activity_to_music_profile(activity_info)
    
    assert "preferred_genres" in music_profile
    assert "preferred_moods" in music_profile
    assert 0.0 <= music_profile["energy"] <= 1.0
    assert 0.0 <= music_profile["acousticness"] <= 1.0


def test_retrieve_songs_for_task_returns_ranked_list():
    """Test that retrieval ranks songs appropriately."""
    songs = [
        {
            "id": 1,
            "title": "Lofi Study",
            "artist": "Chill Artist",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.25,
            "tempo_bpm": 80,
            "valence": 0.5,
            "danceability": 0.2,
            "acousticness": 0.85,
        },
        {
            "id": 2,
            "title": "Upbeat Pop",
            "artist": "Pop Artist",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.85,
            "tempo_bpm": 128,
            "valence": 0.8,
            "danceability": 0.8,
            "acousticness": 0.15,
        },
    ]
    
    math_profile = {
        "preferred_genres": ["lofi", "ambient"],
        "preferred_moods": ["chill", "focused"],
        "energy": 0.25,
        "acousticness": 0.85,
        "valence": 0.5,
        "danceability": 0.2,
        "tempo": 0.4,
    }
    
    retrieved = retrieve_songs_for_task(math_profile, songs)
    assert len(retrieved) == 2
    # The lofi song should rank higher for a math study task
    assert retrieved[0]["id"] == 1


def test_build_study_playlist_respects_duration():
    """Test that playlist building respects duration targets."""
    songs = [
        {
            "id": i,
            "title": f"Song {i}",
            "artist": "Artist",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.3,
            "tempo_bpm": 80,
            "valence": 0.5,
            "danceability": 0.2,
            "acousticness": 0.8,
        }
        for i in range(1, 6)
    ]
    
    playlist, total_minutes, _ = build_study_playlist(songs, duration_minutes=75)
    
    assert len(playlist) > 0
    assert len(playlist) <= len(songs)
    # 75 minutes / ~3.5 min per song = ~21 songs, but we only have 5, so should get all 5
    assert total_minutes > 0


def test_build_study_playlist_handles_empty_list():
    """Test that playlist builder handles edge cases gracefully."""
    playlist, total_minutes, status = build_study_playlist([], duration_minutes=60)
    
    assert len(playlist) == 0
    assert total_minutes == 0.0
    assert "No songs" in status or "invalid" in status.lower()


def test_build_study_playlist_warns_when_sparse():
    """Test that playlist warns when not enough songs match."""
    songs = [
        {
            "id": 1,
            "title": "Only Song",
            "artist": "Artist",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.3,
            "tempo_bpm": 80,
            "valence": 0.5,
            "danceability": 0.2,
            "acousticness": 0.8,
        }
    ]
    
    playlist, total_minutes, status = build_study_playlist(songs, duration_minutes=180)
    
    assert len(playlist) == 1
    assert "limited" in status.lower() or "only" in status.lower()
