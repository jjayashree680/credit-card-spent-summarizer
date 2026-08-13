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
# SAMPLE QUESTIONS
# ---------------------------------------------------------

with st.sidebar:

    st.header("Sample Queries")

    sample_queries = [
        "Summarise my spending for March 2026 on card CC-881001",
        "What did I spend the most on last month?",
        "How much did I spend internationally this billing cycle?",
        "Compare my spending this month vs last month",
        "How many reward points did I earn this month and what is their value?",
        "Am I on track to meet the annual fee waiver threshold?",
    ]

    for sample in sample_queries:

        if st.button(
            sample,
            key=sample,
            use_container_width=True,
        ):
            st.session_state.selected_query = sample


# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

selected_query = st.session_state.get(
    "selected_query",
    "",
)

query = st.chat_input(
    "Ask about your credit card spending..."
)


if selected_query:
    query = selected_query
    st.session_state.selected_query = ""


# ---------------------------------------------------------
# SEND QUERY
# ---------------------------------------------------------

if query:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):

        with st.spinner("Analyzing your spending..."):

            try:

                response = requests.post(
                    API_URL,
                    json={
                        "query": query,
                        "thread_id": "streamlit-user",
                    },
                    timeout=120,
                )

                if response.status_code == 200:

                    result = response.json()

                    answer = result.get(
                        "answer",
                        str(result),
                    )

                    st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                else:

                    error_message = (
                        f"API Error: {response.status_code}\n\n"
                        f"{response.text}"
                    )

                    st.error(error_message)

            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to FastAPI. "
                    "Make sure the FastAPI server is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. "
                    "Please try again."
                )

            except Exception as e:

                st.error(
                    f"Unexpected error: {e}"
                )