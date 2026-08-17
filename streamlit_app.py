import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/api/v1/query/"


st.set_page_config(
    page_title="Credit Card Spend Summarizer",
    page_icon="💳",
    layout="wide",
)


st.title("💳 Credit Card Spend Summarizer")

st.caption(
    "Ask questions about your spending, rewards, "
    "international transactions, and fee waiver progress."
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("Chat")

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []

        # Optional: reset conversation thread
        st.session_state.thread_id = "streamlit-user"

        st.rerun()


# ---------------------------------------------------------
# THREAD ID
# ---------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-user"


# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

query = st.chat_input(
    "Ask about your credit card spending..."
)


# ---------------------------------------------------------
# SEND QUERY
# ---------------------------------------------------------

if query:

    # Show user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    # Assistant
    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = requests.post(
                    API_URL,
                    json={
                        "query": query,
                    },
                    timeout=120,
                )

                if response.status_code == 200:

                    result = response.json()

                    answer = result.get(
                        "answer",
                        "I couldn't generate a response.",
                    )

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                else:

                    st.error(
                        f"API Error: {response.status_code}\n\n"
                        f"{response.text}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to FastAPI. "
                    "Make sure the FastAPI server is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. Please try again."
                )

            except Exception as e:

                st.error(
                    f"Unexpected error: {e}"
                )