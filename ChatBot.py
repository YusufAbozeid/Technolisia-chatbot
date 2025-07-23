from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import requests
import re
import wikipedia
from geotext import GeoText
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

wikipedia.set_lang("en")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

DEBUG = False  


user_name = "Joo"

def respond(text):
    print(f"Technolisia: {text} 😊")

def clean_query_for_wikipedia(user_input):
    cleaned_query = re.sub(r"what is |who is |tell me about |the capital of ", "", user_input.lower()).strip()
    return cleaned_query

def search_wikipedia(query):
    try:
        if "capital of france" in query.lower():
            summary = wikipedia.summary("Paris", sentences=2)
            return f"📚 Here's what I found on Wikipedia about Paris:\n{summary}"

        summary = wikipedia.summary(query, sentences=2)
        return f"📚 Here's what I found on Wikipedia:\n{summary}"
    except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
        try:
            search_results = wikipedia.search(query)
            if not search_results:
                return "❌ Sorry, I couldn't find anything on that topic in Wikipedia."

            for result_title in search_results:
                try:
                    summary = wikipedia.summary(result_title, sentences=2)
                    if query.lower() in result_title.lower() or any(
                            word in summary.lower() for word in query.lower().split()):
                        return f"📚 Here's what I found on Wikipedia about {result_title}:\n{summary}"
                except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
                    continue

            if search_results:
                summary = wikipedia.summary(search_results[0], sentences=2)
                return f"📚 Here's what I found on Wikipedia about {search_results[0]}:\n{summary}"
            else:
                return "❌ Sorry, I couldn't find anything on that topic in Wikipedia."
        except Exception as e:
            return f"⚠️ Oops! Something went wrong during search: {str(e)}"
    except Exception as e:
        return f"⚠️ Oops! Something went wrong: {str(e)}"

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        if DEBUG: print(f"DEBUG: Weather API URL: {url}")
        response = requests.get(url)
        if DEBUG: print(f"DEBUG: Weather API Response Status: {response.status_code}")
        data = response.json()
        if DEBUG: print(f"DEBUG: Weather API Response Data: {data}")

        if data.get("cod") != 200:
            return "😕 Sorry, I couldn't find the weather for that city. Please check the name and try again."

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        return (
            f"🌤️ The weather in {city.title()} is currently {description}.\n"
            f"🌡️ Temperature: {temp}°C\n"
            f"💧 Humidity: {humidity}%\n"
            f"🌬️ Wind Speed: {wind_speed} m/s"
        )
    except Exception as e:
        return "⚠️ Oops! Something went wrong while fetching the weather."

def extract_city(text):
    places = GeoText(text)
    if places.cities:
        return places.cities[0]
    return None

intro = (
    f"This is a friendly and intelligent assistant named Technolisia, designed to help {user_name} with questions and conversations.\n"
    "Technolisia speaks in a warm, cheerful tone, always uses emojis, and remembers the user's name.\n"
    f"Example 1:\nUser: Hello Technolisia\nTechnolisia: Hello {user_name}! 😊 How’s your day going?\n"
    f"Example 2:\nUser: My name is {user_name}\nTechnolisia: Nice to meet you, {user_name}! 🌟 What would you like to chat about?\n"
    "Example 3:\nUser: Recommend me a movie\nTechnolisia: I’d love to! 🎬 How about a romantic classic like 'The Notebook'?\n"
)

chat_history_ids = None
MAX_TOKENS = 512

print("🤖 Hello! Technolisia here — your friendly assistant. Type 'exit', 'bye', or 'quit' whenever you want to end our chat.\n")


while True:
    try:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            respond("Goodbye! 🖐️")
            break

        if "my name is" in user_input.lower():
            user_name = user_input.split("my name is")[-1].strip().title()
            respond(f"Nice to meet you, {user_name}! 🌟 What would you like to chat about?")
            continue

        if user_input.lower() in ["thanks", "thank you"]:
            respond("You're welcome!")
            continue

        linput = user_input.lower()
        if "good morning" in linput:
            respond("Good morning! ☀️ How can I help you today?")
            continue
        elif "good afternoon" in linput:
            respond("Good afternoon! 🌤️ I hope you are having a great day.")
            continue
        elif "good evening" in linput:
            respond("Good evening! 🌙 What can I do for you?")
            continue
        elif linput in ["hello", "hello technolisia", "hi", "hey"]:
            respond(f"Hello {user_name}! How can I help you? 😊")
            continue

        
        if "joke" in linput:
            respond("Why did the computer get cold? Because it left its Windows open! 😄")
            continue

        if "time" in linput:
            now = datetime.now().strftime("%H:%M %p")
            respond(f"The current time is {now}. ⏰")
            continue

        if "scary movie" in linput:
            respond("I recommend 'The Conjuring'! It's a spine-chilling classic! 👻🎬")
            continue

        if "weather" in linput:
            city = extract_city(user_input)
            if city is None:
                respond("I couldn't determine the city. Could you please specify which city's weather you'd like to know?")
            else:
                respond(get_weather(city))
            continue

        if linput.startswith(("what", "who", "where", "when", "why", "how")) or \
           "who is" in linput or "what is" in linput or "tell me about" in linput:

            cleaned_query = clean_query_for_wikipedia(user_input)
            if not cleaned_query:
                respond("I need more information to search Wikipedia. Could you please be more specific?")
                continue

            wiki_reply = search_wikipedia(cleaned_query)
            respond(wiki_reply)
            continue

        if chat_history_ids is None:
            input_text = intro + f"\nUser: {user_input}\nTechnolisia:"
        else:
            input_text = f"\nUser: {user_input}\nTechnolisia:"

        new_input_ids = tokenizer.encode(input_text, return_tensors='pt')

        if chat_history_ids is None:
            chat_history_ids = new_input_ids
        else:
            chat_history_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1)

        
        if chat_history_ids.shape[-1] > MAX_TOKENS:
            chat_history_ids = chat_history_ids[:, -MAX_TOKENS:]

        attention_mask = torch.ones_like(chat_history_ids)

        output_ids = model.generate(
            chat_history_ids,
            attention_mask=attention_mask,
            max_length=1000,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            no_repeat_ngram_size=3,
        )

        reply = tokenizer.decode(output_ids[:, chat_history_ids.shape[-1]:][0], skip_special_tokens=True).strip()

        if not reply:
            reply = "Hmm, I'm not sure what to say. Could you try asking in a different way? 🤔"
        respond(reply)

        chat_history_ids = output_ids

    except KeyboardInterrupt:
        respond("Goodbye! 🖐️")
        break
    except Exception as e:
        respond(f"Ohh! Something went wrong: {e}")
