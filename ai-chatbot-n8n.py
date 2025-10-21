import streamlit as st
import requests
import json

# --- Configuration ---
# IMPORTANT: Replace this with your actual n8n Webhook URL.
# You can find this in your Webhook node in n8n after saving and activating the workflow.
try:
    N8N_WEBHOOK_URL = st.secrets.n8n_webhook_url
except (AttributeError, KeyError):
    st.error("Webhook URL not found in st.secrets. Please check your .streamlit/secrets.toml file.")
    st.stop()

# --- Streamlit UI ---
st.set_page_config(page_title="Vijay's AI Chatbot", page_icon="🤖")
st.title("🤖Vijay's n8n Powered AI Chatbot :robot:")
st.write("Enter your message below and let the AI respond!")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input ---
if prompt := st.chat_input("What's on your mind?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare payload for n8n webhook
                # The 'question' key here assumes your Webhook node in n8n is set to expect
                # a JSON body where the user's message is under a key named 'question'.
                # Adjust 'question' if your Webhook expects a different key.
                payload = {"question": prompt}

                # Send request to n8n webhook
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

                # Assuming n8n returns a JSON response with a 'text' field
                # that contains the AI's answer.
                # Adjust 'text' if your 'Respond to Webhook' node uses a different key.
                n8n_response_data = response.json()
                if isinstance(n8n_response_data, list) and n8n_response_data:
                    ai_response = n8n_response_data[0].get("text")
                elif isinstance(n8n_response_data, dict):
                     ai_response = n8n_response_data.get("text")
                else:
                    ai_response = "Error: Unexpected response format from n8n."
                    st.error(f"Unexpected response from n8n: {n8n_response_data}")

                if ai_response:
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                else:
                    st.error("AI did not return a valid response text.")
                    st.session_state.messages.append({"role": "assistant", "content": "Error: Could not get a valid AI response."})


            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with n8n webhook: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: Could not connect to n8n ({e})"})
            except json.JSONDecodeError:
                st.error(f"Error decoding JSON response from n8n. Raw response: {response.text}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: Invalid JSON from n8n ({response.text})"})
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"An unexpected error occurred ({e})"})
