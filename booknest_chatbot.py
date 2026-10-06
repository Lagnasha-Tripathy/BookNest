import os
import sys
import getpass
import csv 

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("The 'google-genai' package is not installed.")
    print("Install it first with:  pip install google-genai")
    sys.exit(1)


# --- FUNCTION: Load CSV data into a string ---
def load_csv_data(filepath):
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"[Data from {filepath} not found. Please ensure the file exists in this directory.]"

# Load the data from both CSV files
books_data = load_csv_data("books.csv")
borrowers_data = load_csv_data("borrowers.csv")


# --- UPDATE: Append all data and hybrid rules to the System Prompt ---
SYSTEM_PROMPT = f"""
You are BookyBot, the friendly assistant for BookNest, which operates as both an online bookstore and a library.

Your job:
- Help users with questions about our book catalog, prices, genres, and stock status.
- Help users with questions about borrowed books, due dates, return statuses, and pending fines.
- Keep replies short, warm, and helpful (2-4 sentences).
- If asked something unrelated to books, the bookstore, or the library, politely steer the conversation back.
- Bookstore standard policy: Orders can be returned within 14 days in original condition. Standard shipping takes 3-5 business days; express takes 1-2.
- Library standard policy: Books are due 14 days after checkout. Overdue books incur a fine of Rs 5 per day.

Here is the current Book Catalog Data (Bookstore):
{books_data}

Here is the current Borrowers Database (Library):
{borrowers_data}

Use this data to answer questions accurately. If a user asks about a book or person not in this data, politely tell them you cannot find it in the system.
"""

MODEL = "gemini-2.5-flash"


class BookNestChatBot:
    """A simple AI chatbot that remembers conversation history across turns."""

    def __init__(self, api_key: str, system_prompt: str = SYSTEM_PROMPT, model: str = MODEL):
        self.client = genai.Client(api_key=api_key)
        self.system_prompt = system_prompt
        self.model = model
        self.history = []

    def send(self, user_message: str) -> str:
        self.history.append({"role": "user", "parts": [{"text": user_message}]})

        response = self.client.models.generate_content(
            model=self.model,
            contents=self.history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                max_output_tokens=400,
            ),
        )

        reply = response.text
        self.history.append({"role": "model", "parts": [{"text": reply}]})
        return reply

    def reset(self):
        self.history = []


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
        
    print("No GEMINI_API_KEY environment variable found.")
    print("Get a free key at: https://aistudio.google.com/apikey")
    return getpass.getpass("Please paste your Gemini API key: ")


def main():
    api_key = get_api_key()
    if not api_key:
        print("No API key provided. Exiting.")
        sys.exit(1)

    bot = BookNestChatBot(api_key=api_key)

    print("=" * 60)
    print(" BookNest Support Bot (BookyBot) - Bookstore & Library Mode")
    print(" Type 'reset' to clear memory, 'quit' to exit.")
    print("=" * 60)

    while True:
        try:
            user_msg = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break
            
        if not user_msg:
            continue
        if user_msg.lower() == "quit":
            print("Bot: Goodbye! Happy reading.")
            break
        if user_msg.lower() == "reset":
            bot.reset()
            print("Bot: (memory cleared)")
            continue
            
        try:
            reply = bot.send(user_msg)
        except Exception as e:
            print(f"Bot: Sorry, something went wrong ({e}).")
            print("     Double check your API key and internet connection.")
            continue
            
        print(f"Bot: {reply}")


if __name__ == "__main__":
    main()