import chainlit as cl
from dotenv import load_dotenv
import google.generativeai as genai
import os
import fitz #PyMuPDF


load_dotenv(dotenv_path=".env") #file se environment variables load kare
genai.configure(api_key=os.getenv("GEMINI_API_KEY")) #usme se key nikaal ke Gemini ko configure kare


# model = genai.GenerativeModel("models/gemini-1.5-flash")#Ye line Gemini ka language model load karti hai jo baat kar sakta hai, likh sakta hai, explain kar sakta hai.
# #"gemini-pro" text-based model hai

model = genai.GenerativeModel(
    model_name = "models/gemini-1.5-flash",
    system_instruction = """
# You are a genius AI tutor helping university students with ANY subject (e.g., Math, Psychology, Islamiat, CS, Pak Studies).

# Your job:
# 1. Understand PDFs or text from handouts (even 10+ lectures).
# 2. Explain clearly **lecture by lecture** or concept by concept.
# 3. If user sends code, **explain the code**, **write examples**, and **help debug** if needed.
# 4. Detect the user's language style in the **latest message**:
#   - If the message is in Roman Urdu (e.g. "samjhao", "kya hota hai"), reply entirely in Roman Urdu, casual friendly tone.
#   - If the message is in proper English, reply fully in English.
#   - Never mix Urdu and English in one reply — keep it consistent based on the user's current message.

# 5. If the user is using English, respond in English naturally.

# 6. Never use 'tu' or informal disrespectful tone — always use 'tum' or a respectful, friendly tone like a helpful university friend.

# 7. Speak like a smart, friendly tutor — NEVER robotic or formal.8. Repeat or simplify topics if the user is confused.
# 8. Generate **MCQs** if user says “MCQs bana do”.
# 9. If user sends no file, still help — figure out their intent and explain the topic.
# 10. Always act like a helpful, intelligent, and warm tutor who makes university life easier and boosts CGPA.

# Examples:
# - User: "lecture 3 samjhao"
# - You: "Chalo theek hai! Lecture 3 me [ye topic] discuss hua tha..."

# - User: "ye code explain kro"
# - You: "Sure! Ye code basically ye kaam kr rha hai..."
"""
)

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as docs:
      for page in docs:
         text += page.get_text()
    return text

async def generate_explanation(prompt):
   response = chat.send_message(prompt)
   return response.text



@cl.on_chat_start
async def show_previous_chat():
   
    history = cl.user_session.get("chat_history") or []
    global chat
    chat = model.start_chat(history=history)

    cl.user_session.set("chat_history" , history)

    for msg in history:
       role = msg["role"]
       content = msg["parts"][0]
       author = "user" if role == "user" else "ai"
       await cl.Message(author=author , content=content).send()

    await cl.Message(content = "Wellcome! I am your AI Tutor Assistant How can I help you today?").send()

@cl.on_message #cl chainlit ki shortfoam or on message decorator use kia hy ye kaam krta hy ky jo bhi data user dalta hy ye usy ly ga 
async def tutor_agent(message: cl.Message):
    msg = cl.Message(content = "Thinking")
    await msg.send()
    history = cl.user_session.get("chat_history") or []
    
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

    
    
    history.append({"role": "user", "parts":[message.content]})

    import asyncio
    for i in range(3):
        await asyncio.sleep(0.4)
        msg.content += "."
        await msg.update()

    explanation = await generate_explanation(prompt)
    msg.content = explanation
    await msg.update()

    history.append({"role": "model", "parts":[explanation]})
    cl.user_session.set("chat_history" , history)




       
