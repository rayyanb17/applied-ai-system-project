# 🎧 Model Card - Music Recommender & AI Playlist Generator

## 1. Model Name

Playlist 1.0 (Original Recommender) + PlaylistGen 1.0 (AI Playlist Generator)

---

## 2. Intended Use

### Original Recommender (PlayList 1.0)

Recommends songs that match a user's explicitly stated preferences across 8 musical dimensions (genre, mood, energy, tempo, acousticness, valence, danceability, artist affinity). For classroom exploration only, not for real users.

### AI Playlist Generator (PlaylistGen 1.0)

Generates personalized playlists by parsing natural language requests for any activity (workout, road trip, studying, relaxation, parties, creative work, etc.) and retrieving relevant songs from the catalog. Intended for users needing instant background music for any context. Uses RAG to retrieve activity-relevant songs before generating the playlist output.

---

## 3. How the Models Work

### Original Model (Rule-Based Scoring)

1. User provides explicit preferences (genre, mood, energy targets, etc.)
2. System scores each song as weighted Euclidean distance from user preferences
3. Tempo is normalized to 0-1 scale for comparability
4. Genre and mood matches are binary (add weight if match, else 0)
5. Numerical features use distance: score = 1 - |feature_value - target|
6. All component scores are weighted and summed
7. Top-scoring songs are returned with match explanations

### New Model (RAG-Based AI Playlist Generator)

1. **Activity Request Parsing** (AI-powered with Gemini or regex fallback):
   - Extract duration (minutes), activity type (workout, road trip, study, party, relax, creative, etc.), preferred genres, energy level, vibe
   - Uses Gemini API if available; gracefully falls back to regex patterns
2. **Activity-to-Music Profile** (Fine-tuned activity-specific mappings):
   - Each activity type maps to preferred genres, moods, and numeric targets
   - Example: workout → electronic/pop/hip-hop, energetic/intense mood, energy=0.80, acousticness=0.15
   - Example: study → lofi/ambient/classical, chill/focused mood, energy=0.25, acousticness=0.80
3. **RAG Retrieval** (Retrieve before ranking):
   - Scores all songs against the activity profile
   - Prioritizes genre/mood matches (highest weight)
   - Includes numeric feature similarity
   - Returns ranked list of all candidate songs
4. **Playlist Generation**:
   - Selects top-N songs to reach target duration
   - Estimates ~3.5 minutes per song
   - Returns playlist, total duration, and status message

---

## 4. Data

- **Catalog Size**: 18 songs
- **Genres**: pop, lofi, rock, ambient, synthwave, jazz, reggae, classical, metal, indie pop, edm, rnb, country, blues, folk
- **Moods**: happy, chill, intense, moody, relaxed, nostalgic, dreamy, aggressive, euphoric, romantic, reflective, wistful, tender, focused
- **Features per Song**: title, artist, genre, mood, energy (0-1), tempo (BPM), valence (0-1), danceability (0-1), acousticness (0-1)
- **Data Changes**: Expanded from ~10 songs to 18 by combining starter set with curated additions
- **Coverage**: Multiple genres and moods represented; some niche preferences (e.g., "k-pop", "melancholy") missing

---

## 5. Strengths

### Original Recommender

- Transparent scoring logic; easy to explain why a song was recommended
- Handles sparse user profiles gracefully (uses sensible defaults)
- Efficient ranking (no ML training needed)
- Deterministic output (same input = same output)

### AI Playlist Generator

- **RAG advantage**: Retrieval step filters to activity-relevant songs before final ranking, improving quality
- Intelligent activity request parsing via Gemini API handles varied natural language input
- Activity-specific fine-tuned profiles work well for common scenarios (workouts, road trips, studying, relaxation, parties)
- Graceful fallback to regex when Gemini is unavailable
- Clear user feedback at each step (duration extracted, music profile built, playlist generated)

---

## 6. Limitations and Bias

### Original Recommender

- Limited dataset (18 songs): Many niche genres/moods will have zero or one match
- Genre and mood weights (0.19, 0.14) may overpower numeric features
- No diversity constraint: "top N songs" might all be very similar
- Out-of-range inputs (energy > 1.0) are clamped but not warned in user output
- Cold-start problem: New users with no preference history get defaults

### AI Playlist Generator

- **Activity parsing errors**: Unusual activity descriptions may be misinterpreted (e.g., "I need upbeat music for a workout" → system may infer upbeat = energetic correctly, but complex requests could fail)
- **Sparse catalog**: Small dataset means many activity types (hiking, gaming, competitive sports) have no ideal matches
- **Duration estimation**: Fixed 3.5-minute average is unrealistic; long songs + short songs equally counted
- **No user feedback loop**: Genre/mood mismatches in activity recommendations aren't learned; same patterns repeat
- **Activity coverage bias**: 9 predefined activity types; anything outside (e.g., "music for meditation") falls to generic "general" handling
- **Fair access gap**: Requires Gemini API key (costs $, may fail), though regex fallback still works

### Fairness Concerns

- **Genre bias**: Electronic/synthwave overrepresented in "coding" profile; underrepresents classical or jazz as coding music
- **Cultural bias**: Dataset has minimal representation of non-Western genres (e.g., no K-pop, Indian classical, African genres beyond reggae)
- **Disability access**: No support for low-bandwidth retrieval or audio descriptions; relies on text-based query parsing
- **Language bias**: Gemini parsing optimized for English task descriptions; other languages may fail

---

## 7. Evaluation

### Original Recommender Evaluation

- **Tested profiles**: 6 user profiles including edge cases (conflicting preferences, out-of-range values, sparse inputs)
- **Checked for**: Correct ranking, graceful fallback, consistent explanations
- **Results**: Recommender correctly prioritized matching genres/moods; handling of out-of-range inputs is silent (no user warning)

### AI Playlist Generator Evaluation

- **Activity parsing**: Tested with "90 minute workout", "2 hours road trip", "45 min study session" → all parsed correctly
- **RAG retrieval**: Verified lofi/ambient songs rank highest for study profile; high-energy songs rank highest for workout
- **Playlist generation**: Confirmed duration targets are respected (within +/- 1 song)
- **Fallback behavior**: Disabled API, confirmed regex fallback produces valid activity profiles
- **Edge cases**: Empty catalog → returns empty playlist with warning; 1-song catalog → returns 1 song + warns user

### Metrics

- **Determinism**: Run same request 5 times → identical playlist output ✓
- **Coverage**: Workout activity matches 7/18 songs; study activity matches 8/18 songs; road trip matches 6/18 songs
- **Quality**: Manual spot-check of workout playlist confirmed high-energy and dance-friendly songs as expected

---

## 8. Future Work

### Short-term (Immediate Improvements)

- Add real song duration metadata to CSV; replace 3.5-minute average
- Expand catalog to 100+ songs to reduce sparseness
- Add user feedback loop: thumbs up/down on generated playlists to refine profiles
- Support multi-genre task descriptions: "lofi AND upbeat" → blend two profiles

### Medium-term (New Features)

- Diversity constraints: Enforce no-artist-repeats in playlists
- Mood transitions: "start calm, build to energetic" → sequence songs by energy arc
- Live Gemini integration: Stream song recommendations as user describes task, refine on the fly
- Comparative explanations: "Why this song over that one?"

### Long-term (Advanced)

- Fine-tune a small language model on activity-based music preferences (replaces Gemini API)
- Collaborative filtering: Learn from multiple users' playlist thumbs-up/down
- Audio feature extraction: Use Spotify API for richer audio features (timbre, loudness, etc.)
- Cross-domain RAG: Retrieve from multiple music catalogs (Spotify, YouTube Music) not just local dataset

---

## 9. Personal Reflection

Building a RAG system revealed how crucial **retrieval quality** is to final output. The original recommender scored all 18 songs every time; the RAG version filters early, which changes behavior significantly. For a study activity, the original recommender might rank an upbeat pop song highly if energy happens to be 0.3; the RAG version explicitly excludes pop because it's not in the "preferred_genres" list for study, regardless of numeric features. This is better for activity-specific use but also a form of **hard constraint bias** — the system will never recommend a fun pop song for studying, even if the user would love it.

The Gemini activity parsing was surprising: it handled natural language variations ("I need music for 90 mins of workouts", "two hour road trip", "background music for coding all night") that pure regex would miss. But it also introduced **API dependency risk** and cost. The fallback regex layer is crucial for reliability and helps me understand the tradeoff between flexibility (AI) and robustness (rules).

One misconception I had: I thought RAG meant "add a retrieval step and accuracy goes up." In reality, RAG only helps if retrieval improves over full ranking. For a small catalog, this is clear. For a large catalog, bad retrieval can hurt (miss good songs). This taught me RAG is about **smart filtering** first, ranking second.

If I built this in production, I'd invest in:

1. **Real user feedback**: Track which recommended songs users actually add to their playlists
2. **Ongoing dataset curation**: Monitor underrepresented genres/moods
3. **Fairness monitoring**: Log which communities' task types work well vs. poorly
4. **Cost controls**: Evaluate whether Gemini API cost is worth the UX gain over regex
