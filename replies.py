# replies.py
import os
import openai
import random

# ===== OPENAI CONFIG =====
openai.api_key = os.getenv("OPENAI_KEY")

# ===== BAD WORDS =====
BAD_WORDS = [
    "badword1",
    "badword2",
    "badword3",
    # add more words you want to filter
]

# ===== FALLBACK REPLIES =====
FALLBACK_REPLIES = [
    "🤖 I am learning new things every day!",
    "😎 Interesting! Tell me more.",
    "🤔 Can you explain that differently?",
    "👍 Got it!",
    "😊 Thanks for sharing!"
]

# ---------- GET REPLY ----------
def get_reply(message=None):
    """
    If message is provided, try AI reply using OpenAI API.
    If fails, return a random fallback reply.
    """
    if not message:
        return random.choice(FALLBACK_REPLIES)

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=message,
            temperature=0.7,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        reply = response.choices[0].text.strip()
        if reply:
            return reply
        else:
            return random.choice(FALLBACK_REPLIES)
    except Exception as e:
        # In case OpenAI fails or key is missing
        print(f"OpenAI Error: {e}")
        return random.choice(FALLBACK_REPLIES)
