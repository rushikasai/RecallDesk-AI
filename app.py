
import os
import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

# App configuration
st.set_page_config(
    page_title="RecallDesk AI",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 RecallDesk AI")
st.caption("Customer support that remembers.")

# Hindsight configuration
API_KEY = os.getenv("HINDSIGHT_API_KEY")
BASE_URL = os.getenv(
    "HINDSIGHT_API_URL",
    "https://api.hindsight.vectorize.io"
)

BANK_ID = "recalldesk-customers"

@st.cache_resource
def get_client():
    return Hindsight(
        base_url=BASE_URL,
        api_key=API_KEY
    )

if not API_KEY:
    st.warning(
        "Hindsight API key is not configured yet. "
        "Add HINDSIGHT_API_KEY before using the chatbot."
    )
    st.stop()

try:
    client = get_client()
except Exception as error:
    st.error(f"Could not connect to Hindsight: {error}")
    st.stop()

# Create the memory bank
if "bank_ready" not in st.session_state:
    st.session_state.bank_ready = False

if not st.session_state.bank_ready:
    if st.button("Connect RecallDesk Memory"):
        try:
            client.create_bank(
                bank_id=BANK_ID,
                name="RecallDesk Customer Support",
                background=(
                    "Long-term memory for customer support "
                    "conversations and preferences."
                )
            )
            st.session_state.bank_ready = True
            st.success("Memory bank created!")
            st.rerun()
        except Exception as error:
            st.error(
                f"Could not create memory bank: {error}"
            )

    st.info(
        "Create the memory bank before starting a conversation."
    )
    st.stop()

# Conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Customer message
prompt = st.chat_input("How can we help you today?")

if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            # Store the customer's message
            client.retain(
                bank_id=BANK_ID,
                content=f"Customer said: {prompt}",
                context="Customer support conversation"
            )

            # Retrieve relevant memories
            memories = client.recall(
                bank_id=BANK_ID,
                query=prompt
            )

            memory_context = "\n".join(
                memory.text for memory in memories.results
            )

            # Generate a contextual response
            response = client.reflect(
                bank_id=BANK_ID,
                query=(
                    f"Customer message: {prompt}\n"
                    f"Relevant memories: {memory_context}\n"
                    "Respond helpfully using relevant customer "
                    "memories. Do not invent customer details."
                )
            )

            answer = response.text
            st.write(answer)

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as error:
            st.error(f"Something went wrong: {error}")

# Clear conversation display
if st.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()
