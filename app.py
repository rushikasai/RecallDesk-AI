

import os
import streamlit as st
from hindsight_client import Hindsight

st.set_page_config(
    page_title="RecallDesk AI",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 RecallDesk AI")
st.caption("Customer support that remembers previous conversations.")

# Hindsight configuration
API_KEY = st.secrets.get("HINDSIGHT_API_KEY", "")
API_URL = st.secrets.get(
    "HINDSIGHT_API_URL",
    "https://api.hindsight.vectorize.io"
)
BANK_ID = st.secrets.get("HINDSIGHT_BANK_ID", "recalldesk")

if not API_KEY:
    st.warning("Please configure your Hindsight API key in Streamlit Secrets.")
    st.stop()

customer_id = st.text_input(
    "Customer ID",
    placeholder="Example: customer001"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("How can we help you?")

if user_input:
    if not customer_id.strip():
        st.error("Please enter a Customer ID first.")
        st.stop()

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    try:
        with Hindsight(
            base_url=API_URL,
            api_key=API_KEY
        ) as client:

            memory_result = client.recall(
                bank_id=BANK_ID,
                query=f"Customer ID: {customer_id}. Find relevant previous support conversations."
            )

            previous_memories = [
                memory.text for memory in memory_result.results
            ]

            client.retain(
                bank_id=BANK_ID,
                content=(
                    f"Customer ID: {customer_id}\n"
                    f"Customer message: {user_input}"
                ),
                context="Customer support conversation",
                metadata={"customer_id": customer_id}
            )

            response = client.reflect(
                bank_id=BANK_ID,
                query=(
                    "You are a helpful customer support assistant. "
                    f"Customer ID: {customer_id}. "
                    f"Previous relevant memories: {previous_memories}. "
                    f"Current question: {user_input}. "
                    "Give a clear and helpful answer. "
                    "Do not invent company policies or facts."
                )
            )

            answer = response.text

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant"):
            st.write(answer)

    except Exception as error:
        st.error(f"Something went wrong: {error}")
