# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

Give your model a short, descriptive name.

PlayList 1.0

---

## 2. Intended Use

Describe what your recommender is designed to do and who it is for.

Prompts:

- What kind of recommendations does it generate
- What assumptions does it make about the user
- Is this for real users or classroom exploration

The recommender tries to find the songs that most closely match the user's preference, assuming that they have at least one in the given features. Due to the limited dataset, it is not suited for real world use yet, but as the dataset expands, real world users might actually be able to use this and find songs they like.

---

## 3. How the Model Works

Explain your scoring approach in simple language.

Prompts:

- What features of each song are used (genre, energy, mood, etc.)
- What user preferences are considered
- How does the model turn those into a score
- What changes did you make from the starter logic

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

The features that are considered are genre, mood, energy, tempo, valence, danceability, acousticness, and artist, with the user giving their preference in those values. It then essentially finds the weighted closeness of songs to the user's preferences, and recommends the highest scored songs, which indicates the closest songs.

---

## 4. Data

Describe the dataset the model uses.

Prompts:

- How many songs are in the catalog
- What genres or moods are represented
- Did you add or remove data
- Are there parts of musical taste missing in the dataset

## There were ten songs originally in the database, and I added 8, making a total of eighteen songs in the database. There are multiple genre's represented, such as metal, pop, rock, lofi, country, and blues, as well as a wide range of moods like aggressive, chill, relaxed, nostalgic, dreamy, and romantic.

## 5. Strengths

Where does your system seem to work well

Prompts:

- User types for which it gives reasonable results
- Any patterns you think your scoring captures correctly
- Cases where the recommendations matched your intuition

Honestly, I think it gave reasonable results in every case. In some of the cases, the features were not all there, and yet the model was output recommendations that made sense. In some of the cases, the closeness value not high, but that as shown to user to explain that. The biggest limitation here is the limited dataset, and if that gets expanded, then the recommender would work a lot better.

---

## 6. Limitations and Bias

Where the system struggles or behaves unfairly.

Prompts:

- Features it does not consider
- Genres or moods that are underrepresented
- Cases where the system overfits to one preference
- Ways the scoring might unintentionally favor some users

Because genre and mood are huge part of the weight, if a song'ss genre and mood match, then those might overpower and go ahead of songs whose other characteristics match more closely. Additionally, due to the limited number of songs in the database, the user might find that number of songs the system recommends that they like might be limited. This is especially true for users who like a niche type of song that is limited or not in the database.

---

## 7. Evaluation

How you checked whether the recommender behaved as expected.

Prompts:

- Which user profiles you tested
- What you looked for in the recommendations
- What surprised you
- Any simple tests or comparisons you ran

No need for numeric metrics unless you created some.

I tested six user profiles: a balanced baseline, a conflicting profile (ambient + aggressive + high energy), unknown category values, out-of-range energy, artist-bias stress, and a sparse numeric-only profile. For each one, I looked at whether the top songs matched the intent and whether the explanation text actually reflected the factors that mattered for that profile.

What I looked for most was whether genre and mood were overpowering everything else, and whether the artist bonus could hijack results. In the baseline case, the output felt correct, and in the artist stress test, the recommender still picked the better overall match first, so the artist signal stayed small.

The biggest surprise was that out-of-range inputs (like energy above 1.0) still produced normal-looking results instead of throwing an error or warning. Another interesting outcome was that unknown genre/mood values forced the system to rely on numeric similarity only, which worked but made recommendations feel more generic.

As a simple check, I reran the same profiles multiple times and got consistent rankings, and I also verified that explanations only referenced profile fields that were actually provided.

---

## 8. Future Work

Ideas for how you would improve the model next.

Prompts:

- Additional features or preferences
- Better ways to explain recommendations
- Improving diversity among the top results
- Handling more complex user tastes

The biggest thing that would need to be done next would be expanding the song dataset. The current limited dataset can result in the recommender outputting songs with low closeness values. Additionally, the songs recommended should not be too close to the users preference ensuring a great diversity in the songs recommended.

---

## 9. Personal Reflection

A few sentences about your experience.

Prompts:

- What you learned about recommender systems
- Something unexpected or interesting you discovered
- How this changed the way you think about music recommendation apps

Recommendation algoritihms are a lot more complicated than I thought they would be. There are many different ways to do a recommendation algorithim, and each one can have a massive effect on the recommendations. Fine tuning the weights to give good recommendations can be an arduous process as well.
