import random
import os
import time
import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- Helpers ---
def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip() for line in file if line.strip()]
    return words

def speak(text, pause=0, voice="com.apple.voice.compact.en-US.Samantha", rate=165):
    os.system(f'say -v {voice} -r {rate} "{text}"')
    if pause > 0:
        time.sleep(pause)

def get_meaning(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data[0]["meanings"][0]["definitions"][0]["definition"]
        else:
            return "Sorry, no meaning found."
    except Exception as e:
        return f"Error fetching meaning: {e}"

def spell_word(word):
    speak("The correct spelling is:", pause=1)
    for letter in word:
        speak(letter.lower(), pause=0.1)
    speak(word, pause=1)
    return " ".join(word.upper())

# --- Quiz state ---
words = load_words("words.txt")
random.shuffle(words)
score = 0
index = 0
show_next = False   # flag to control Next button

# --- HTML template ---
TEMPLATE = """
<!doctype html>
<title>Spelling Quiz</title>
<h1>Spelling Quiz</h1>
<p>Score: {{ score }} / {{ total }}</p>
{% if word %}
<p>Spell the Word:</p>
{% endif %}
<form method="post">
    <input type="text" name="spelling" placeholder="Type the spelling here">
    <button name="action" value="submit">Submit Spelling</button>
    <button name="action" value="rep">Repeat Word</button>
    <button name="action" value="ans">Answer (Spell)</button>
    <button name="action" value="mean">Meaning</button>
    {% if show_next %}
    <button name="action" value="next">Next Word</button>
    {% endif %}
    <button name="action" value="quit">Quit</button>
</form>
<p>{{ message|safe }}</p>
"""

@app.route("/", methods=["GET", "POST"])
def quiz():
    global index, score, show_next
    message = ""

    if index >= len(words):
        return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"

    word = words[index]
    
    # --- NEW: automatically speak the first word when quiz starts ---
    if request.method == "GET" and index == 0:
        speak("Spell the word.", pause=0)
        speak(word, pause=1)

    if request.method == "POST":
        action = request.form["action"]
        spelling = request.form.get("spelling", "").strip().lower()

        if action == "submit":
            if spelling == word.lower():
                score += 1
                speak("Correct!", pause=1)
                index += 1
                show_next = False  # reset next button
                if index < len(words):
                    word = words[index]
                    message = "Correct! Next word"
                    speak("Next word.", pause=0)
                    speak(word, pause=1)
                else:
                    return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"
            else:
                message = "That's not correct."
                speak("That's not correct.", pause=1)

        elif action == "rep":
            speak("Spell the word.", pause=0)
            speak(word, pause=1)

        elif action == "ans":
            spelling_str = spell_word(word)
            message = f"The correct spelling is: <b>{spelling_str}</b><br>(Word: {word})"
            show_next = True   # enable Next button

        elif action == "mean":
            meaning = get_meaning(word)
            message = f"Meaning: {meaning}"
            speak(f"The meaning of {word} is: {meaning}", pause=0)

        elif action == "next":
            index += 1
            show_next = False  # hide Next button again
            if index < len(words):
                word = words[index]
                message = "Next word!"
                speak("Next word.", pause=0)
                speak(word, pause=1)
            else:
                return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"

        elif action == "quit":
            speak(f"You scored {score} out of {len(words)}.", pause=1)
            speak("Goodbye!", pause=1)
            return f"<h1>Quiz stopped!</h1><p>Final Score: {score} / {len(words)}</p><p>Goodbye!</p>"


    return render_template_string(TEMPLATE, word=word, score=score, total=len(words), message=message, show_next=show_next)

if __name__ == "__main__":
    app.run(debug=True)
