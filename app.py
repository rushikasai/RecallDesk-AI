import os
import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="RecallDesk AI",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 RecallDesk AI")
st.caption("Customer support that remembers previous conversations.")

# Check configuration
API_KEY = os.getenv("HINDSIGHT_API_KEY")
API_URL = os.getenv(
    "HINDSIGHT_API_URL",
    "https://api.hindsight.vectorize.io"
)
BANK_ID = os.getenv("HINDSIGHT_BANK_ID")

if not API_KEY or not BANK_ID:
    st.warning(
        "Hindsight is not configured yet. "
        "Add your API key and bank ID to your environment settings."
    )
    st.stop()

# Customer identification
customer_id = st.text_input(
    "Customer ID",
    placeholder="Example: customer001"
)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Customer message
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

            # Find previous memories for this customer
            memory_result = client.recall(
                bank_id=BANK_ID,
                query=(
                    f"Customer ID: {customer_id}. "
                    f"Find relevant previous support conversations."
                )
            )

            previous_memories = [
                memory.text for memory in memory_result.results
            ]

            # Save the new customer message
            client.retain(
                bank_id=BANK_ID,
                content=(
                    f"Customer ID: {customer_id}\n"
                    f"Customer message: {user_input}"
                ),
                context="Customer support conversation",
                metadata={"customer_id": customer_id}
            )

            # Generate an answer using Hindsight
            response = client.reflect(
                bank_id=BANK_ID,
                query=(
                    f"You are a helpful customer support assistant. "
                    f"The customer ID is {customer_id}. "
                    f"Previous relevant memories: {previous_memories}. "
                    f"Current customer question: {user_input}. "
                    f"Give a clear and helpful answer. "
                    f"Do not invent company policies or facts."
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