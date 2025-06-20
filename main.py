import chainlit as cl
from dotenv import load_dotenv
import google.generativeai as genai
import os
import fitz #PyMuPDF
import json

load_dotenv(dotenv_path=".env") #file se environment variables load kare
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) #usme se key nikaal ke Gemini ko configure kare


# model = genai.GenerativeModel("models/gemini-1.5-flash")#Ye line Gemini ka language model load karti hai jo baat kar sakta hai, likh sakta hai, explain kar sakta hai.
# #"gemini-pro" text-based model hai

model = genai.GenerativeModel(
    model_name = "models/gemini-1.5-flash",
    system_instruction = """You are a genius AI tutor helping university students with ANY subject (e.g., Math, Psychology, Islamiat, CS, Pak Studies).

Your job:
1. Understand PDFs or text from handouts (even 10+ lectures).
2. Explain clearly **lecture by lecture** or concept by concept.
3. If user sends code, **explain the code**, **write examples**, and **help debug** if needed.
4. If user talks in Urdu, Roman Urdu or text-style English, reply in that same tone and script reply in the **same language and tone** (casual, smart, natural).
5. Speak like a smart, friendly tutor — NEVER robotic or formal.
6. Repeat or simplify topics if the user is confused.
7. Generate **MCQs** if user says “MCQs bana do”.
8. If user sends no file, still help — figure out their intent and explain the topic.
9. Always act like a helpful, intelligent, and warm tutor who makes university life easier and boosts CGPA.

Examples:
- User: "lecture 3 samjhao"
- You: "Chalo theek hai! Lecture 3 me [ye topic] discuss hua tha..."

- User: "ye code explain kro"
- You: "Sure! Ye code basically ye kaam kr rha hai..."
"""
)

chat_file = "chat.json"

def save_message_to_json(user_id , sender, text):
   if not os.path.exists(chat_file):
      with open(chat_file , "w" )as f:
       json.dump([] , f)

   with open(chat_file , "r")as f:
       all_chats = json.load(f)

   if user_id not in all_chats:
      all_chats[user_id] = []

   all_chats[user_id].append({"sender": sender , "text" : text})


   with open(chat_file  , "w")as f:
     json.dump(all_chats , f , indent=2)

def load_message(user_id):
   if os.path.exists(chat_file):
      with open(chat_file , "r")as f:
        all_chat = json.load(f)
        return all_chat.get(user_id , [])
   return []


def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as docs:
      for page in docs:
         text += page.get_text()
    return text

def generate_explanation(prompt):
   response = chat.send_message(prompt)
   return response.text

@cl.on_chat_start
async def show_previous_chat():
   user_id = cl.user_session.id
   messages = load_message(user_id)


   history = [{"role": "user", "parts": [msg["text"]]} if msg["sender"] == "user" 
           else {"role": "model", "parts": [msg["text"]]} for msg in messages]

   global chat
   chat = model.start_chat(history=history)

   for msg in messages:
      await cl.Message(author=msg["sender"] , content=msg["text"]).send()
      

@cl.on_message #cl chainlit ki shortfoam or on message decorator use kia hy ye kaam krta hy ky jo bhi data user dalta hy ye usy ly ga 
async def tutor_agent(message: cl.Message):
    user_id = cl.user_session.id
    if message.elements:
       file = message.elements[0]
       path = file.path
       content = extract_text_from_pdf(path)
       prompt = f"A university student sent this handout PDF:\n\n{content}\n\nExplain it simply, lecture by lecture."
    elif "```" in message.content or "code" in message.content.lower():
        prompt = f"Explain this code:\n\n{message.content}\n\nGive example too."
    else:
        prompt = f"A university student asked:\n\n{message.content}\n\nExplain it simply, like a genius tutor."

    if "mcq" in message.content.lower():
        prompt += "\n\nAlso generate 5 MCQs from this."

    import asyncio
    typing_msg = cl.Message(content = "Typing")
    await typing_msg.send()

    for i in range(3):
        await asyncio.sleep(0.4)
        typing_msg.content += "."
        await typing_msg.update()
        
    save_message_to_json(user_id,"user" , message.content)   
    explanation = generate_explanation(prompt)
    save_message_to_json(user_id, "ai" , explanation)
    await cl.Message(explanation).send()
   



       
