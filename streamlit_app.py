# import requests
# import streamlit as st
# import uuid

# API_URL = "http://127.0.0.1:8000/api/v1/query/"


# st.set_page_config(
#     page_title="Credit Card Spend Summarizer",
#     page_icon="💳",
#     layout="wide",
# )


# st.title("💳 Credit Card Spend Summarizer")

# st.caption(
#     "Ask questions about your spending, rewards, "
#     "international transactions, and fee waiver progress."
# )


# # ---------------------------------------------------------
# # SESSION STATE
# # ---------------------------------------------------------

# if "messages" not in st.session_state:
#     st.session_state.messages = []


# # ---------------------------------------------------------
# # SIDEBAR
# # ---------------------------------------------------------

# with st.sidebar:

#     st.header("Chat")

#     if st.button(
#         "🗑️ Clear Chat",
#         use_container_width=True,
#     ):
#         st.session_state.messages = []

#         # Optional: reset conversation thread
#         st.session_state.thread_id = str(uuid.uuid4())

#         st.rerun()


# # ---------------------------------------------------------
# # THREAD ID
# # ---------------------------------------------------------


# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = str(uuid.uuid4())

# # ---------------------------------------------------------
# # DISPLAY CHAT HISTORY
# # ---------------------------------------------------------

# for message in st.session_state.messages:

#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])


# # ---------------------------------------------------------
# # USER INPUT
# # ---------------------------------------------------------

# query = st.chat_input("Ask about your credit card spending...")


# # ---------------------------------------------------------
# # SEND QUERY
# # ---------------------------------------------------------

# if query:

#     # Show user message
#     st.session_state.messages.append(
#         {
#             "role": "user",
#             "content": query,
#         }
#     )

#     with st.chat_message("user"):
#         st.markdown(query)

#     # Assistant
#     with st.chat_message("assistant"):

#         with st.spinner("Thinking..."):

#             try:

#                 response = requests.post(
#                     API_URL,
#                     json={
#                         "query": query,
#                         "thread_id": st.session_state.thread_id,
#                         "chat_history": st.session_state.messages,
#                     },
#                     timeout=120,
#                 )

#                 if response.status_code == 200:

#                     result = response.json()

#                     answer = result.get(
#                         "answer",
#                         "I couldn't generate a response.",
#                     )

#                     st.markdown(answer)

#                     st.session_state.messages.append(
#                         {
#                             "role": "assistant",
#                             "content": answer,
#                         }
#                     )

#                 else:

#                     st.error(
#                         f"API Error: {response.status_code}\n\n" f"{response.text}"
#                     )

#             except requests.exceptions.ConnectionError:

#                 st.error(
#                     "Cannot connect to FastAPI. "
#                     "Make sure the FastAPI server is running."
#                 )

#             except requests.exceptions.Timeout:

#                 st.error("The request timed out. Please try again.")

#             except Exception as e:

#                 st.error(f"Unexpected error: {e}")

import uuid
import requests
import streamlit as st

STREAM_API_URL = "http://127.0.0.1:8000/api/v1/query/stream"

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

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

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

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
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

query = st.chat_input("Ask about your credit card spending...")

# ---------------------------------------------------------
# SEND QUERY
# ---------------------------------------------------------

if query:

    # Display user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message("user"):
        st.markdown(query)

    # Display assistant response

    with st.chat_message("assistant"):

        placeholder = st.empty()

        # Show thinking message
        placeholder.markdown("Thinking...")

        try:

            response = requests.post(
                STREAM_API_URL,
                json={
                    "query": query,
                    "thread_id": st.session_state.thread_id,
                    "chat_history": st.session_state.messages,
                },
                stream=True,
                timeout=120,
            )

            if response.status_code != 200:

                st.error(f"API Error: {response.status_code}\n\n" f"{response.text}")

            else:

                answer = ""

                for chunk in response.iter_content(
                    chunk_size=None,
                    decode_unicode=True,
                ):

                    if chunk:

                        # Remove "Thinking..." when first chunk arrives
                        if not answer:
                            placeholder.empty()

                        answer += chunk

                        placeholder.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to FastAPI. " "Make sure the FastAPI server is running."
            )

        except requests.exceptions.Timeout:

            st.error("The request timed out. Please try again.")

        except Exception as e:

            st.error(f"Unexpected error: {e}")

            if response.status_code != 200:

                st.error(f"API Error: {response.status_code}\n\n" f"{response.text}")

            else:

                answer = ""

                for chunk in response.iter_content(
                    chunk_size=None,
                    decode_unicode=True,
                ):

                    if chunk:

                        answer += chunk

                        placeholder.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to FastAPI. " "Make sure the FastAPI server is running."
            )

        except requests.exceptions.Timeout:

            st.error("The request timed out. Please try again.")

        except Exception as e:

            st.error(f"Unexpected error: {e}")
