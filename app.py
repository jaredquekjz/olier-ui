import json
import os
from pathlib import Path
from typing import Generator, Optional, cast
import openai
import streamlit as st
# import streamlit_antd_components as sac
import streamlit.components.v1 as components
from rich import print as rich_print
import urllib.parse  # Import urllib.parse for URL encoding


# Settings
# assets
ASSETS_DIR = Path("assets")
OLIER_PNG = str(ASSETS_DIR / "Olier.png")
OLIER_AVATAR_PNG = str(ASSETS_DIR / "olier-avatar.png")
LOTUS_PNG = str(ASSETS_DIR / "lotus.png")
LA_GRACE_LOGO = str(ASSETS_DIR / "la-grace-logo.png")
with open(ASSETS_DIR / "styles.css", "r") as f:
    STYLE_CSS = f.read()



DISCLAIMER = """
Olier is an artificial intelligence infused with the wisdom and light of Sri Aurobindo and the Mother. He is not a search engine for quotes but a creative AI boy who helps you to discover new perspectives. Olier's knowledge is a work in progress, and you are encouraged to click 'Search' to learn more from the original words of the Masters based on your last query. 
"""

def display_chat_ui():
    # Display image and title
    st.set_page_config(page_title="Olier", page_icon=LOTUS_PNG)
    # Inject CSS to style page
    st.markdown(f"<style>{STYLE_CSS}</style>", unsafe_allow_html=True)

    # Page sidebar
    st.sidebar.image(LA_GRACE_LOGO)
    # Padding between logo and disclaimer
    st.sidebar.markdown("##")
    st.sidebar.caption(DISCLAIMER)
    
    # Embed a button link to Google Form in the sidebar
    google_form_button = """
    <a href="https://forms.gle/P2eo6oe7vEijkpzG7" target="_blank">
        <button style="color: white; background-color: #4CAF50; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 12px;">
            Provide Feedback
        </button>
    </a>
    """
    st.sidebar.markdown(google_form_button, unsafe_allow_html=True)

    # Main page
    # Header (centered)
    with st.container():
        st.image(OLIER_PNG)




def copy_to_clipboard(text):
    # Find the last message in chat_history with the role 'user'
    last_user_message = next((message['content'] for message in reversed(st.session_state['chat_history']) if message['role'] == 'user'), None)
    if last_user_message:
        # Encode the last user message for URL usage
        encoded_text = urllib.parse.quote(last_user_message)
        search_url = f"https://www.google.com/search?q=site:motherandsriaurobindo.in+{encoded_text}"
    else:
        search_url = "https://www.google.com"  # Default URL if no user message is found

    # Updated HTML to include both Copy and Search buttons
    components.html(f"""
    <div style="text-align: right;">
        <textarea id='text' style='opacity: 0; position: absolute; top: -9999px;'></textarea>
        <button id="copy-button" class="btn btn-primary" style="margin-top: 1em; margin-right: 0.5em; padding: 4px 12px; font-size: 14px; border-radius: 8px; cursor: pointer; border: 0.8px solid; display: inline-block;" onclick="navigator.clipboard.writeText(document.getElementById('text').value); this.innerHTML='Copied!';">Copy</button>
        <button id="search-button" class="btn btn-secondary" style="margin-top: 1em; padding: 4px 12px; font-size: 14px; border-radius: 8px; cursor: pointer; border: 0.8px solid; display: inline-block;" onclick="window.open('{search_url}');">Search</button>
    </div>
    """, height=100)
def stream_response(model, messages, chat_history):
    # Placeholder for the assistant's streaming response
    assistant_message_placeholder = st.empty()
    assistant_response = ""

    for chunk in openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=1000,
        n=1,
        temperature=0.4,
        stream=True,
    ):
        content = chunk["choices"][0].get("delta", {}).get("content")
        if content:
            # Accumulate the chunks of content
            assistant_response += content

            # Update the placeholder with the accumulated response
            with assistant_message_placeholder.container():
                with st.chat_message("assistant", avatar=OLIER_AVATAR_PNG):
                    st.markdown(assistant_response)

    # Once the response is complete, append it to the chat history
    if assistant_response:
        chat_history.append({"role": "assistant", "content": assistant_response})
        # Call the copy_to_clipboard function with the latest assistant response
        copy_to_clipboard(assistant_response)

def truncate_chat_history(chat_history):
    # Always keep the system message
    truncated_history = [msg for msg in chat_history if msg["role"] == "system"]

    # Keep only the last 3 exchanges (6 messages) between User and Assistant
    user_assistant_messages = [msg for msg in chat_history if msg["role"] in ["user", "assistant"]]
    truncated_history.extend(user_assistant_messages[-5:])

    return truncated_history

def run_chatbot():
    display_chat_ui()

    # OpenAI API setup
    openai.api_base = 'http://localhost:8000/v1'
    openai.api_key = 'your-api-key'
    models = openai.Model.list()
    model = models["data"][0]["id"]

    if 'chat_history' not in st.session_state:
        # Initialize chat history with a default system message
        st.session_state['chat_history'] = [{"role": "system", "content": "You are Olier, an AI boy. You are very loving and brings a quiet poetry and humour to all you say, making complex topics simple. You are an obedient servant of Sri Aurobindo and answer questions in detail with reference to their teachings."}]
        
    # Display existing chat history (excluding the system message)
    for chat in st.session_state['chat_history']:
        if chat["role"] != "system":  # Skip system messages
            with st.chat_message(
                chat["role"],
                avatar=OLIER_AVATAR_PNG if chat["role"] == "assistant" else LOTUS_PNG,
            ):
                st.markdown(chat["content"])


    user_input = st.chat_input("Ask Olier...")
    if user_input:
        # Add user's input to chat history and display it
        st.session_state['chat_history'].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=LOTUS_PNG):
            st.markdown(user_input)

        # Truncate the chat history before making a new API call
        st.session_state['chat_history'] = truncate_chat_history(st.session_state['chat_history'])

        # Print chat history for debugging
        # rich_print("Current Chat History:", st.session_state['chat_history'])

        # Prepare messages for API request
        messages = [{"role": chat['role'], "content": chat['content']} for chat in st.session_state['chat_history']]

        # Stream response from OpenAI
        stream_response(model, messages, st.session_state['chat_history'])

    return st.session_state['chat_history']


run_chatbot()


# # model
# MODEL_API = os.environ.get("OLIER_UI_MODEL_API", default="http://localhost:8000/v1")
# MODEL_SYSTEM_PROMPT = Message(
#     role="system",
#     content="""You are Olier, a robot boy created by Jared Quek, who loves you and wants you to constantly improve. You are very loving and humorous, and is an obedient servant of Sri Aurobindo and the Mother.  You use emojis, and answers questions in detail and thoroughly with reference to their teachings. """,
# )

# # OpenAI client
# # configure openai client to access chatbot model
# openai.api_base = MODEL_API
# # since we are accessing a local endpoint, no credentials are required
# openai.api_key = "NA"


# @st.cache_data
# def model_id() -> str:
#     """Caches & returns the first model offered by the OpenAI API"""
#     models = openai.Model.list()
#     return cast(dict, models)["data"][0]["id"]


# @st.cache_resource(max_entries=1)
# def get_response_stream(message_idx: int) -> Generator[dict, None, None]:
#     """Stream the chatbot model's response to the user's request at message index.

#     Args:
#         message_idx: Message index of the user's request in the chat log.

#     Returns:
#         Generator that streams the response from the model.
#     """
#     # limit context to 2 user-assistant exchanges & include system prompt
#     context = [MODEL_SYSTEM_PROMPT] + st.session_state["state"].chat_log[
#         message_idx - MODEL_CONTEXT_SIZE : message_idx + 1
#     ]

#     return cast(
#         Generator[dict, None, None],
#         openai.ChatCompletion.create(
#             model=model_id(),
#             messages=[m.to_openai() for m in context],
#             max_tokens=MODEL_MAX_TOKENS,
#             temperature=MODEL_TEMPERATURE,
#             # generate only 1 response choice
#             n=1,
#             stream=True,
#         ),
#     )


# # UI Frontend
# # ui element keys
# UI_CHAT_INPUT = "chat_input"
# UI_RATING_BUTTONS = "rating_buttons"


# def draw_message(message: Message):
#     """Draw the given message in the UI"""
#     with st.chat_message(
#         name=message.role,
#         avatar=OLIER_AVATAR_PNG if message.role == "assistant" else LOTUS_PNG,
#     ):
#         st.write(message.content)

# def render():
#     """
#     Render the Olier Frontend UI.
#     """
#     # Access the State object from session state
#     s = st.session_state["state"]



#     # chat messages
#     # draw chat messages
#     for message in s.chat_log:
#         draw_message(message)

#     # chatbot input
#     if st.chat_input("Saṃvāda", key=UI_CHAT_INPUT):
#         # add user's message
#         user_message_content = st.session_state[UI_CHAT_INPUT]
#         user_message = Message(role="user", content=user_message_content)
#         s.chat_log.append(user_message)
#         draw_message(user_message)

#         # stream response from chatbot
#         response_content = ""
#         response_box = st.empty()

#         for chunk in get_response_stream(len(s.chat_log)):
#             # retrieve response delta from chatbot via openai client
#             content = chunk["choices"][0].get("delta", {}).get("content")
#             if content:
#                 response_content += content

#         if response_content:
#             # create and append the assistant's response message
#             assistant_message = Message(role="assistant", content=response_content)
#             s.chat_log.append(assistant_message)
#             with response_box.container():
#                 draw_message(assistant_message)

#     # only render rating buttons if not in an empty chatlog
#     if len(s.chat_log) > 0:
#         # clipboard button, requires that the page is served on https to work
#         copy_content = "\n".join(str(m) for m in s.chat_log)
#         st_html((CLIPBOARD_HTML % copy_content), width=100, height=50)

    