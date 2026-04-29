"""
Activity/context parser for playlist generation.
Uses Gemini API to intelligently parse user requests and map them to music profiles.
Supports any activity: workouts, road trips, studying, relaxing, focus work, etc.
"""

import logging
import os
from typing import Dict, Optional

# ===== PASTE YOUR GEMINI API KEY HERE =====
GEMINI_API_KEY = "Your API Key Here"
# ==========================================

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


def _get_gemini_client():
    """Initialize Gemini client if API key is available."""
    if not GEMINI_AVAILABLE:
        return None
    
    api_key = GEMINI_API_KEY.strip()
    if not api_key or api_key == "your-gemini-api-key-here":
        logger.warning("GEMINI_API_KEY not set in task_parser.py. Using fallback regex parser.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        logger.error("Failed to initialize Gemini: %s", e)
        return None


def _check_input_sufficiency(user_input: str, client) -> Dict:
    """
    Use Gemini to determine if user input has enough information to parse.
    
    Returns:
        Dict with "is_sufficient" (bool) and optional "reason" (str)
    """
    try:
        prompt = f"""Is this user input sufficient to create a music playlist? The input must describe or imply an activity/context.

User input: "{user_input}"

Answer with ONLY a JSON object (no markdown, no extras):
{{"is_sufficient": true/false}}

Examples of SUFFICIENT input:
- "I need music for a 90 minute workout"
- "road trip playlist"
- "music for studying"
- "give me some party music"

Examples of INSUFFICIENT input (too vague, no context):
- "Hi"
- "Hello"
- "Music"
- "Test"
- "Yeah"
- "What"
- "None"
"""
        
        response = client.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        import json
        result = json.loads(response_text)
        return {"is_sufficient": bool(result.get("is_sufficient", True))}
        
    except Exception as e:
        logger.warning("Sufficiency check failed: %s. Assuming input is sufficient.", e)
        return {"is_sufficient": True}


def parse_activity_request(user_input: str) -> Dict:
    """
    Parse a user's activity/context request into structured info.
    Uses Gemini to intelligently extract duration, activity type, and music preferences.
    
    Args:
        user_input: User's natural language request
                   Examples: "I need music for a 90 minute workout",
                            "give me a road trip playlist for 3 hours",
                            "I want a lot of rap songs good for a race",
                            "music for my cross country trip"
    
    Returns:
        Dict with keys:
        - duration_minutes: int (default 60)
        - activity_type: str (e.g., "workout", "road_trip", "focus_work", "relaxation")
        - preferred_genres: list of str (e.g., ["rap", "hip-hop"])
        - preferred_artists_or_keywords: str (e.g., "Drake", "energetic", "mellow")
        - energy_level: float 0-1 (inferred from activity type)
        - vibe: str (e.g., "energetic", "chill", "focused", "romantic")
    """
    if not user_input or not isinstance(user_input, str):
        logger.warning("Invalid user input for activity parsing: %s", user_input)
        return _default_activity_profile()
    
    client = _get_gemini_client()
    
    # Use Gemini to check if input has sufficient information
    if client:
        sufficiency_check = _check_input_sufficiency(user_input, client)
        if not sufficiency_check["is_sufficient"]:
            logger.warning("User input too vague: '%s'. Asking for clarification.", user_input)
            return {"error": True, "message": "Please describe what you need music for (e.g., 'workout', 'road trip', 'studying', 'relaxation')."}
        
        return _parse_with_gemini(user_input, client)
    else:
        logger.info("Gemini unavailable, using fallback regex parser")
        return _parse_with_fallback(user_input)


def _parse_with_gemini(user_input: str, client) -> Dict:
    """Use Gemini to parse activity/context description."""
    try:
        prompt = f"""Parse this music/playlist request and extract the user's intent:
"{user_input}"

Return ONLY valid JSON (no markdown, no extras) with these fields:
- duration_minutes: integer (default 60 if not mentioned or very unclear)
- activity_type: string (categorize as one of: workout, road_trip, study, focus, relax, party, creative, sleep, cooking, or general)
- preferred_genres: list of strings or empty list (e.g., ["rap", "electronic"] or [])
- preferred_artists_or_keywords: string (e.g., "Drake", "energetic", "chill"; empty string if none)
- energy_level: float between 0.0 (very low/sleepy) and 1.0 (very high/intense), based on activity
- vibe: string (choose one: "energetic", "chill", "focused", "romantic", "party", "uplifting", "mellow", "balanced")

Example output for "I need music for a 90 minute workout":
{{"duration_minutes": 90, "activity_type": "workout", "preferred_genres": [], "preferred_artists_or_keywords": "", "energy_level": 0.8, "vibe": "energetic"}}

Example output for "give me a lot of rap songs for a race":
{{"duration_minutes": 60, "activity_type": "workout", "preferred_genres": ["rap", "hip-hop"], "preferred_artists_or_keywords": "", "energy_level": 0.85, "vibe": "energetic"}}"""
        
        response = client.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean markdown if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        import json
        result = json.loads(response_text)
        
        # Validate and clamp values
        activity_profile = {
            "duration_minutes": max(1, int(result.get("duration_minutes", 60))),
            "activity_type": str(result.get("activity_type", "general")).lower(),
            "preferred_genres": [g.strip().lower() for g in result.get("preferred_genres", []) if isinstance(g, str) and g.strip()],
            "preferred_artists_or_keywords": str(result.get("preferred_artists_or_keywords", "")).lower().strip(),
            "energy_level": max(0.0, min(1.0, float(result.get("energy_level", 0.5)))),
            "vibe": str(result.get("vibe", "balanced")).lower(),
        }
        
        logger.info("Parsed activity request with Gemini: %s", activity_profile)
        return activity_profile
        
    except Exception as e:
        logger.error("Gemini parsing failed: %s. Using fallback.", e)
        return _parse_with_fallback(user_input)


def _parse_with_fallback(user_input: str) -> Dict:
    """Fallback regex-based parser for activity requests."""
    import re
    
    user_input_lower = user_input.lower()
    
    # Extract duration
    duration_match = re.search(r"(\d+)\s*(minute|min|hour|hr)", user_input_lower)
    duration = 60
    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(2)
        if "hour" in unit or "hr" in unit:
            duration = value * 60
        else:
            duration = value
    
    # Detect activity type
    activity_keywords = {
        "workout": ["workout", "exercise", "gym", "run", "race", "training", "fitness"],
        "road_trip": ["road trip", "drive", "driving", "car", "travel", "journey", "highway"],
        "study": ["study", "focus", "work", "concentration", "exam", "homework"],
        "relax": ["chill", "relax", "relax", "sleep", "rest", "lounge"],
        "party": ["party", "dance", "club", "DJ", "festival"],
        "creative": ["creative", "write", "design", "code", "art", "produce"],
        "cooking": ["cook", "kitchen", "dinner", "breakfast"],
    }
    
    activity_type = "general"
    for activity, keywords in activity_keywords.items():
        if any(kw in user_input_lower for kw in keywords):
            activity_type = activity
            break
    
    # Extract genre mentions
    genre_keywords = [
        "rap", "hip-hop", "hip hop", "pop", "rock", "electronic", "edm", "jazz",
        "lofi", "lo-fi", "ambient", "classical", "country", "blues", "metal",
        "reggae", "funk", "indie", "folk", "soul", "r&b", "rnb", "punk"
    ]
    preferred_genres = [g.replace(" ", "-") for g in genre_keywords if g in user_input_lower]
    
    # Extract artist mentions (capitalized words that appear 1-2 times = likely artist name)
    words = user_input.split()
    potential_artists = [w.strip(",.!?") for w in words if w[0].isupper() and len(w) > 2 and w not in ["I", "The", "A", "Give", "Music", "Playlist"]]
    artist_keyword = " ".join(potential_artists[:2]) if potential_artists else ""
    
    # Extract energy-related keywords
    energy_mapping = {
        "low": 0.2,
        "chill": 0.3,
        "calm": 0.25,
        "mellow": 0.30,
        "relaxed": 0.35,
        "balanced": 0.5,
        "moderate": 0.5,
        "energetic": 0.75,
        "high": 0.8,
        "intense": 0.9,
        "upbeat": 0.8,
    }
    
    energy_level = 0.5
    for keyword, level in energy_mapping.items():
        if keyword in user_input_lower:
            energy_level = level
            break
    
    # Infer energy from activity type
    activity_energy_map = {
        "workout": 0.80,
        "road_trip": 0.60,
        "study": 0.30,
        "relax": 0.25,
        "party": 0.85,
        "creative": 0.45,
        "cooking": 0.50,
    }
    if activity_type in activity_energy_map and energy_level == 0.5:  # Use activity default if no explicit energy
        energy_level = activity_energy_map[activity_type]
    
    # Infer vibe
    vibe_map = {
        "workout": "energetic",
        "road_trip": "uplifting",
        "study": "focused",
        "relax": "chill",
        "party": "energetic",
        "creative": "balanced",
        "cooking": "balanced",
    }
    vibe = vibe_map.get(activity_type, "balanced")
    
    activity_profile = {
        "duration_minutes": max(1, duration),
        "activity_type": activity_type,
        "preferred_genres": preferred_genres,
        "preferred_artists_or_keywords": artist_keyword,
        "energy_level": energy_level,
        "vibe": vibe,
    }
    
    logger.info("Parsed activity request with fallback regex: %s", activity_profile)
    return activity_profile


def _default_activity_profile() -> Dict:
    """Return a sensible default activity profile."""
    return {
        "duration_minutes": 60,
        "activity_type": "general",
        "preferred_genres": [],
        "preferred_artists_or_keywords": "",
        "energy_level": 0.50,
        "vibe": "balanced",
    }


def activity_to_music_profile(activity_info: Dict) -> Dict:
    """
    Map an activity/context to music preferences.
    
    Args:
        activity_info: Dict from parse_activity_request()
    
    Returns:
        Dict with music preference hints (genres, moods, energy, acousticness, etc.)
    """
    activity_type = activity_info.get("activity_type", "general").lower()
    energy_level = activity_info.get("energy_level", 0.5)
    vibe = activity_info.get("vibe", "balanced").lower()
    
    # Activity-to-music mappings: each activity has preferred genres, moods, and numeric targets
    activity_profiles = {
        "workout": {
            "preferred_genres": ["electronic", "pop", "hip-hop", "edm", "r&b"],
            "preferred_moods": ["energetic", "intense", "aggressive"],
            "target_energy": 0.80,
            "target_acousticness": 0.15,
            "target_valence": 0.70,
            "target_danceability": 0.75,
        },
        "road_trip": {
            "preferred_genres": ["pop", "rock", "indie pop", "hip-hop", "country"],
            "preferred_moods": ["happy", "energetic", "reflective"],
            "target_energy": 0.60,
            "target_acousticness": 0.45,
            "target_valence": 0.70,
            "target_danceability": 0.60,
        },
        "study": {
            "preferred_genres": ["lofi", "ambient", "classical"],
            "preferred_moods": ["chill", "focused", "dreamy"],
            "target_energy": 0.25,
            "target_acousticness": 0.80,
            "target_valence": 0.45,
            "target_danceability": 0.20,
        },
        "focus": {
            "preferred_genres": ["lofi", "ambient", "electronic"],
            "preferred_moods": ["focused", "creative", "calm"],
            "target_energy": 0.30,
            "target_acousticness": 0.60,
            "target_valence": 0.50,
            "target_danceability": 0.25,
        },
        "relax": {
            "preferred_genres": ["ambient", "classical", "jazz", "lofi"],
            "preferred_moods": ["calm", "dreamy", "relaxed"],
            "target_energy": 0.20,
            "target_acousticness": 0.85,
            "target_valence": 0.50,
            "target_danceability": 0.15,
        },
        "party": {
            "preferred_genres": ["electronic", "edm", "pop", "hip-hop", "r&b"],
            "preferred_moods": ["euphoric", "energetic", "happy"],
            "target_energy": 0.85,
            "target_acousticness": 0.10,
            "target_valence": 0.80,
            "target_danceability": 0.90,
        },
        "creative": {
            "preferred_genres": ["indie pop", "electronic", "folk", "jazz"],
            "preferred_moods": ["creative", "contemplative", "uplifting"],
            "target_energy": 0.45,
            "target_acousticness": 0.55,
            "target_valence": 0.60,
            "target_danceability": 0.40,
        },
        "sleep": {
            "preferred_genres": ["ambient", "classical"],
            "preferred_moods": ["dreamy", "calm", "tender"],
            "target_energy": 0.10,
            "target_acousticness": 0.80,
            "target_valence": 0.40,
            "target_danceability": 0.05,
        },
        "cooking": {
            "preferred_genres": ["pop", "indie pop", "jazz"],
            "preferred_moods": ["happy", "relaxed", "creative"],
            "target_energy": 0.50,
            "target_acousticness": 0.60,
            "target_valence": 0.70,
            "target_danceability": 0.50,
        },
    }
    
    # Get base profile for activity, or use balanced default
    base_profile = activity_profiles.get(activity_type, {
        "preferred_genres": ["pop", "indie pop", "electronic"],
        "preferred_moods": ["happy", "balanced", "uplifting"],
        "target_energy": 0.50,
        "target_acousticness": 0.50,
        "target_valence": 0.60,
        "target_danceability": 0.50,
    })
    
    # Adjust energy based on user's energy_level input
    adjusted_energy = base_profile["target_energy"] * (0.6 + 0.4 * energy_level)
    adjusted_energy = max(0.0, min(1.0, adjusted_energy))
    
    # If user specified genres, prioritize them
    final_genres = activity_info.get("preferred_genres") or base_profile["preferred_genres"]
    if not final_genres:
        final_genres = base_profile["preferred_genres"]
    
    music_profile = {
        "preferred_genres": final_genres,
        "preferred_moods": base_profile["preferred_moods"],
        "energy": adjusted_energy,
        "acousticness": base_profile["target_acousticness"],
        "valence": base_profile["target_valence"],
        "danceability": base_profile["target_danceability"],
        "activity_type": activity_type,
        "vibe": vibe,
        "artist_keyword": activity_info.get("preferred_artists_or_keywords", ""),
    }
    
    logger.info("Generated music profile for activity %s: %s", activity_type, music_profile)
    return music_profile


def clarify_user_preferences() -> Optional[Dict]:
    """
    Ask user clarifying questions if retrieval was sparse.
    Returns updated preferences or None if user opts out.
    """
    print("\nNot enough songs found. Let me ask a quick question:")
    print("1. Do you prefer acoustic or electronic sounds? (a/e): ", end="", flush=True)
    preference = input().strip().lower()
    
    if preference == "a":
        return {"acousticness": 0.75}
    elif preference == "e":
        return {"acousticness": 0.25}
    
    return None
