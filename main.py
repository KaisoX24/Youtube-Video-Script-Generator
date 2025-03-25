import streamlit as st
import time
import json
import concurrent.futures
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv('.env')

API_KEY=str(os.getenv('GROQ_API_KEY'))

st.set_page_config(page_title='YouTube Script Generator ',layout="wide",)
st.title('Youtube Video Script Generator')
st.header('Script Maker')

# API initialization
client = Groq(api_key=API_KEY)

VALID_KEYWORDS = [
    "video", "gameplay", "vlog", "tutorial", "reaction", "review", "challenge", "stream", "let's play", "playthrough",
    "unboxing", "commentary", "tips", "guide", "how-to", "review", "streaming", "behind-the-scenes", "exploration", 
    "documentary", "interview", "show", "series", "live", "educational", "discussion", "collaboration", "content",
    "analysis", "opinion", "storytime", "travel", "music video", "skit", "parody", "animation", "sketch", "concept video",
    "sponsored", "advertisement", "music", "gaming", "tech review", "reaction video", "let's talk", "cooking", "fitness",
    "sports", "challenges", "review", "experience", "unboxing", "event coverage", "DIY", "life hacks", "party games"
]

# Helper functions
def is_video_related(topic):
    """Check if the topic is related to video content."""
    topic_lower = topic.lower()
    return any(keyword in topic_lower for keyword in VALID_KEYWORDS)

def save_history(user_input, script):
    """Save the current topic and script to history."""
    history = {"topic": user_input, "script": script}
    try:
        with open("history.json", "a") as file:
            json.dump(history, file)
            file.write("\n")
    except Exception as e:
        print(f"Error saving history: {e}")

def load_history():
    """Load history from the JSON file."""
    try:
        with open("history.json", "r") as file:
            history = [json.loads(line) for line in file.readlines()]
        return history
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def delete_history_entry(topic_to_delete):
    """Delete a specific history entry based on the topic."""
    try:
        # Load current history
        with open("history.json", "r") as file:
            history = [json.loads(line) for line in file.readlines()]

        # Filter out the history entry to delete
        history = [entry for entry in history if entry['topic'] != topic_to_delete]

        # Save the updated history back to the file
        with open("history.json", "w") as file:
            for entry in history:
                json.dump(entry, file)
                file.write("\n")

    except Exception as e:
        print(f"Error deleting history entry: {e}")

def stream_script(script):
    """Stream the script dynamically."""
    full_text = ""
    placeholder = st.empty()
    for char in script:
        full_text += char
        placeholder.text(full_text)
        time.sleep(0.01)

# Caching function for script generation
@st.cache_data
def generate_script_cached(user_input):
    """Cache the generated script based on user input."""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a YouTube video script generator generate in form Title, Intro ,concept, objectives, challenges, storyline, finalresult, Outro. If the topic is good to be generated in this form. "},
                      {"role": "user", "content": f"Generate a YouTube script about {user_input}."}],
            model="llama-3.2-3b-preview", 
            max_tokens=1000)

        if response.choices:
            return response.choices[0].message.content
        else:
            return "Failed to generate script"
    except Exception as e:
        return f"Error: {e}"

# Multithreading for script generation
def generate_script_async(user_input):
    """Generate script in a separate thread."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(generate_script_cached, user_input)
        return future.result()

# Sidebar for Navigation
page = st.sidebar.selectbox("Select Page", ["Generate Script", "View History"])

if page == "Generate Script":
    # Main Screen for Script Generation
    user_input = st.chat_input('Enter the topic')

    if user_input:
        if is_video_related(user_input):
            with st.spinner("Generating script..."):  
                try:  
                    # Run the script generation asynchronously
                    script = generate_script_async(user_input)
                    if script:
                        stream_script(script)
                        # Save the current topic and script to history
                        save_history(user_input, script)
                    else:
                        st.error('Failed to generate script')
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.error("❌ Please enter a the video details.")
    
elif page == "View History":
    # History Screen
    history = load_history()
    if history:
        selected_history = st.selectbox(
            'Select a past topic:',
            [item['topic'] for item in history]
        )

        if selected_history:
            selected_script = next(item['script'] for item in history if item['topic'] == selected_history)
            with st.expander(f"Script for: {selected_history}") :
                st.write(selected_script)

            # Add delete button next to each script
            delete_button = st.button(f"Delete history for '{selected_history}'", key=selected_history)
            if delete_button:
                delete_history_entry(selected_history)
                st.success(f"History for '{selected_history}' has been deleted.")
    else:
        st.write("No history available.")
