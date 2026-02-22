from fastapi import FastAPI
from pydantic import BaseModel
from langchain_groq import ChatGroq
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# Get environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGO_URI")

# Initialize Groq model safely
llm = None
if groq_api_key:
    try:
        llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-8b-instant")
    except Exception as e:
        print(f"Error initializing ChatGroq: {e}")

# Connect to MongoDB safely
collection = None
if mongo_uri:
    try:
        client = MongoClient(mongo_uri)
        db = client["study_bot"]
        collection = db["chat_history"]
    except Exception as e:
        print(f"MongoDB connection error: {e}")

# Pydantic model for POST request
class ChatRequest(BaseModel):
    user_input: str
@app.post("/chat")
def chat(request: ChatRequest):
    user_input = request.user_input

    if llm is None:
        return {"error": "LLM not initialized. Check API key or model name."}

    try:
        # Generate bot response FIRST
        response = llm.invoke(user_input)
        bot_message = response.content

        # Try storing in MongoDB (but don't break if it fails)
        try:
            if collection is not None:
                collection.insert_one({"role": "user", "message": user_input})
                collection.insert_one({"role": "bot", "message": bot_message})
        except Exception as db_error:
            print("MongoDB connection failed:", db_error)

        return {"response": bot_message}

    except Exception as e:
        return {"error": str(e)}
