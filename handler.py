from menu_scrape import fetch_dining_hall_info as get_context
import sqlite3
import json
import os
import logging

import google.generativeai as genai

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger.setLevel(logging.DEBUG)

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")

context = get_context()

this_dir = os.path.dirname(os.path.abspath(__file__))
var_dir = os.path.join(this_dir, 'var')
users_db = os.path.join(var_dir, 'users.db')
conversations_db = os.path.join(var_dir, 'conversations.db')

if not os.path.exists(var_dir):
    os.makedirs(var_dir)

if not os.path.exists(users_db):
    conn = sqlite3.connect(users_db)
    c = conn.cursor()
    c.execute('''CREATE TABLE users
                 (user_id text, preferences json)''')
    conn.commit()
    conn.close()

if not os.path.exists(conversations_db):
    conn = sqlite3.connect(conversations_db)
    c = conn.cursor()
    c.execute('''CREATE TABLE conversations
                 (user_id text, conversation_id text, history json)''')
    conn.commit()
    conn.close()


class Conversation:
    def __init__(self, conversation_id, history=[]):
        self.conversation_id = conversation_id
        self.history = history

class User:
    def __init__(self, user_id, conversations=[]):
        self.user_id = user_id
        self.conversations = conversations

class Handler:
 
    users_db = None #TODO: Implement database
    conversations_db = None #TODO: Implement database

    def __init__(self, user_id=None):
        self.user_id = user_id
        self.user = User(user_id)

    def fetch_database_information(self):
        conn = sqlite3.connect(users_db)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (self.user_id,))
        user = c.fetchone()
        conn.close()
        if user:
            logger.info(f"User {self.user_id} found in database")
            conn = sqlite3.connect(conversations_db)
            c = conn.cursor()
            c.execute("SELECT * FROM conversations WHERE user_id=?", (self.user_id,))
            conversations = c.fetchall()
            conn.close()
            for conversation in conversations:
                logger.info(f"Conversation {conversation[1]} found in database")
                self.user.conversations.append(Conversation(conversation[1], json.loads(conversation[2])))
        else:
            logger.info(f"User {self.user_id} not found in database")

        pass
        #TODO: Fetch user and conversation information from database

    def handle_message(self, message, conversation_id):
        pass
        #TODO: Handle message and update conversation history

    def update_database_information(self):
        pass
        #TODO: Update user and conversation information in database

    def save_preferences(self):
        pass
        #TODO: Save user preferences to database