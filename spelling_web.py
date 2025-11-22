import random
import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# --- Helpers ---
def load_words(file_path):
    with open(file_path, 'r') as file:
        words = [line.strip() for line in file if line.strip()]
    return words

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
    # Return spelling string for display
    return " ".join(word.upper())

# --- Quiz state ---
words = load_words("words.txt")
random.shuffle(words)
score = 0
index = 0
show_next = False   # flag to control Next button

# --- HTML template with browser speech synthesis ---
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
    <button type="button" onclick="speakText('{{ word }}')">Repeat Word</button>
    <button type="button" onclick="spellWord('{{ word }}')">Answer (Spell)</button>
    <button name="action" value="mean">Meaning</button>
    {% if show_next %}
    <button name="action" value="next">Next Word</button>
    {% endif %}
    <button name="action" value="quit">Quit</button>
</form>
<p>{{ message|safe }}</p>

<script>
function speakText(text) {
    if (!text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    speechSynthesis.speak(utterance);
}

function spellWord(word) {
    if (!word) return;
    let delay = 0;
    for (let letter of word) {
        const utterance = new SpeechSynthesisUtterance(letter);
        utterance.rate = 0.9;
        setTimeout(() => speechSynthesis.speak(utterance), delay);
        delay += 600;
    }
    // After spelling letters, speak the full word
    setTimeout(() => {
        const utterance = new SpeechSynthesisUtterance(word);
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
    }, delay + 500);
}

function speakMeaning(text) {
    if (!text) return;
    const utterance = new SpeechSynthesisUtterance("The meaning is: " + text);
    utterance.rate = 0.9;
    speechSynthesis.speak(utterance);
}
</script>
"""

@app.route("/", methods=["GET", "POST"])
def quiz():
    global index, score, show_next
    message = ""
    meaning = ""

    if index >= len(words):
        return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"

    word = words[index]

    if request.method == "POST":
        action = request.form["action"]
        spelling = request.form.get("spelling", "").strip().lower()

        if action == "submit":
            if spelling == word.lower():
                score += 1
                index += 1
                show_next = False
                if index < len(words):
                    word = words[index]
                    message = "Correct! Next word"
                else:
                    return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"
            else:
                message = "That's not correct."

        elif action == "ans":
            spelling_str = spell_word(word)
            message = f"The correct spelling is: <b>{spelling_str}</b><br>(Word: {word})"
            show_next = True

        elif action == "mean":
            meaning = get_meaning(word)
            message = f"Meaning: {meaning}"

        elif action == "next":
            index += 1
            show_next = False
            if index < len(words):
                word = words[index]
                message = "Next word!"
            else:
                return f"<h1>Quiz complete!</h1><p>Final Score: {score} / {len(words)}</p>"

        elif action == "quit":
            return f"<h1>Quiz stopped!</h1><p>Final Score: {score} / {len(words)}</p><p>Goodbye!</p>"

    return render_template_string(
        TEMPLATE,
        word=word,
        score=score,
        total=len(words),
        message=message,
        show_next=show_next,
        meaning=meaning
    )

if __name__ == "__main__":
    app.run(debug=True)
