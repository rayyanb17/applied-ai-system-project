# Music Recommender & AI Playlist Generator

## Original Project

My Modules 1-3 project was a basic music recommender. It used a user's profile and song features like genre, mood, energy, tempo, valence, danceability, and acousticness to suggest songs they would probably like.

## What This Project Does

This version turns a normal text request into a playlist for things like workouts, study sessions, road trips, relaxing, or cooking. I built it this way because it feels more natural than forcing users to fill out a profile first.

## Architecture Overview

The flow is simple: the user types a request, Gemini checks whether it makes sense, Gemini parses the request, the activity gets turned into a music profile, and the retriever ranks the songs before the playlist is built. The system diagram shows that flow and where testing fits.
![alt text](<assets/Gemini Music Recommendation-2026-04-29-010340.png>)

## Setup

1. Install dependencies with `pip install -r requirements.txt`.
2. Add your Gemini API key in src/task_parser.py.
3. Run `python -m src.main`.
4. Pick mode `2` for the AI playlist generator.

## Sample Interactions

- `I need music for a 90 minute workout` -> Gemini parses a workout request and the app builds a high-energy playlist.
- `give me a 2-hour road trip playlist` -> Gemini treats it as a road trip and the retriever leans toward upbeat songs.
- `Hi` -> Gemini flags it as too vague and asks for more detail.

## Design Decisions

I kept the original recommender instead of replacing it, because it is easier to explain and easier to test. Gemini handles the language part, and a fallback path stays in place if the API is unavailable.

The main trade-off is that the catalog is small, so some requests only get decent results instead of perfect ones. I preferred something simple and reliable over something flashy and hard to debug.

## Testing Summary

I use automated tests in tests/test_recommender.py to check parsing, ranking, playlist length, and edge cases. In the latest run, 8 out of 9 tests passed before I updated the vague-input check; after that fix, the parser now rejects unclear input instead of pretending it knows the answer. The code also logs warnings when parsing fails, which makes it easier to see what went wrong.

I did a quick human check too by trying requests like workout and road-trip prompts, and the generated playlists matched the activity better after the clarification guardrail was added.

## Reflection

This project taught me that AI can be very fast and seem very helpful, but it can forget about minor things until you actual go through the code and see what it did, and what it missed.

## Responsibility Reflection

The biggest limitation in this system is the small song catalog, which means some requests still get generic results. There is also some bias toward the activity types and genres I defined, so uncommon requests can be handled less well than common ones.

This can be slightly misused as a user can use a prompt injection to run their own prompt on the Gemini. Fortunately, due to the fact that the system never actually runs anything it gets back from Gemini, just hands it back to the user, and the code makes sure the output is in a JSON format, the danger of this is mitigated.

What surprised me while testing was that a vague prompt like "just give me music" looked harmless at first, but it actually produced weak behavior until I added the clarification rule. That made it clear that reliability is not just about passing tests, but about handling the messy inputs people really type.

The AI gve some pretty good suggestions. For instance, it implemented the Gemini integration very well, including having Gemini return its answer in a specific structure and then using that to create a response to the user. However, there was one suggestion that was not good. When determining if an input had too little information to create a playlist, it created a whole complicted function with keywords and such to determine if more information was needed, rather than simply just asking Gemini if more information was needed.
