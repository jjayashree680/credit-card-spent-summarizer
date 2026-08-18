import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()


STREAM_API_URL = "http://127.0.0.1:8000/api/v1/query/stream"
API_URL = "http://127.0.0.1:8000/api/v1/query/"
INGEST_API_URL = "http://127.0.0.1:8000/api/v1/ingest/"


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Credit Card Spend Summarizer",
    page_icon="💳",
    layout="wide",
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "role" not in st.session_state:
    st.session_state.role = None

if "username" not in st.session_state:
    st.session_state.username = None

if "selected_query" not in st.session_state:
    st.session_state.selected_query = ""


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

def show_login():

    st.title("💳 Credit Card Spend Summarizer")

    st.caption(
        "Please select how you want to continue."
    )

    col1, col2 = st.columns(2)

    # -----------------------------------------------------
    # ADMIN LOGIN
    # -----------------------------------------------------

    with col1:

        st.subheader("🔐 Admin Login")

        admin_username = st.text_input(
            "Username",
            key="login_username",
        )

        admin_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login as Admin",
            use_container_width=True,
        ):

            expected_username = os.getenv(
                "ADMIN_USERNAME",
                "admin",
            )

            expected_password = os.getenv(
                "ADMIN_PASSWORD",
                "admin123",
            )

            if (
                admin_username == expected_username
                and admin_password == expected_password
            ):

                st.session_state.role = "admin"
                st.session_state.username = admin_username
                st.session_state.messages = []
                st.session_state.thread_id = str(uuid.uuid4())

                st.rerun()

            else:

                st.error(
                    "Invalid admin username or password."
                )

    # -----------------------------------------------------
    # GUEST LOGIN
    # -----------------------------------------------------

    with col2:

        st.subheader("👤 Guest")

        guest_name = st.text_input(
            "Your name",
            placeholder="Enter your name",
            key="guest_name",
        )

        if st.button(
            "Continue as Guest",
            use_container_width=True,
        ):

            st.session_state.role = "guest"

            st.session_state.username = (
                guest_name.strip()
                if guest_name.strip()
                else "Guest"
            )

            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())

            st.rerun()


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

def logout():

    st.session_state.role = None
    st.session_state.username = None
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.selected_query = ""

    st.rerun()


# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------

if st.session_state.role is None:

    show_login()

    st.stop()


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.title("💳 Credit Card Spend")

    st.caption(
        f"👤 {st.session_state.username}"
    )

    st.caption(
        f"Role: {st.session_state.role.title()}"
    )

    st.divider()

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------

    if st.session_state.role == "admin":

        page = st.radio(
            "Navigation",
            [
                "💬 Chat",
                "📚 Knowledge Base",
                "📄 Document Management",
            ],
        )

    else:

        page = st.radio(
            "Navigation",
            [
                "💬 Chat",
                "📚 Knowledge Base",
            ],
        )

    st.divider()

    # -----------------------------------------------------
    # CLEAR CHAT
    # -----------------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.session_state.thread_id = str(
            uuid.uuid4()
        )

        st.session_state.selected_query = ""

        st.rerun()

    # -----------------------------------------------------
    # LOGOUT
    # -----------------------------------------------------

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):

        logout()


# =========================================================
# KNOWLEDGE BASE
# =========================================================

if page == "📚 Knowledge Base":

    st.title("📚 Knowledge Base")

    st.caption(
        "Information available to the Credit Card Spend Assistant."
    )

    st.subheader("You can ask about")

    col1, col2 = st.columns(2)

    with col1:

        st.write("• Credit card policies")
        st.write("• Rewards and points")
        st.write("• International spending")

    with col2:

        st.write("• Fee waiver")
        st.write("• Billing information")
        st.write("• Card benefits")

    st.info(
        "Use the Chat page to ask questions about "
        "credit card policies and benefits."
    )

    st.stop()


# =========================================================
# DOCUMENT MANAGEMENT
# ADMIN ONLY
# =========================================================

if page == "📄 Document Management":

    st.title("📄 Document Management")

    st.caption(
        "Upload documents to update the knowledge base."
    )

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "doc", "txt"],
        help=(
            "Upload a PDF, DOCX, DOC or TXT document "
            "for ingestion."
        ),
    )

    if uploaded_file is not None:

        st.caption(
            f"Selected: {uploaded_file.name}"
        )

        if st.button(
            "📥 Upload & Ingest",
            use_container_width=True,
        ):

            with st.spinner(
                "Uploading and ingesting document..."
            ):

                try:

                    response = requests.post(
                        INGEST_API_URL,
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=300,
                    )

                    if response.status_code == 200:

                        result = response.json()

                        st.success(
                            result.get(
                                "message",
                                "Document ingested successfully.",
                            )
                        )

                    else:

                        st.error(
                            "Ingestion failed:\n\n"
                            + response.text
                        )

                except requests.exceptions.ConnectionError:

                    st.error(
                        "Cannot connect to FastAPI. "
                        "Make sure the FastAPI server is running."
                    )

                except requests.exceptions.Timeout:

                    st.error(
                        "Document ingestion timed out. "
                        "Please try again."
                    )

                except Exception as e:

                    st.error(
                        f"Unexpected error during ingestion: {e}"
                    )

    st.stop()


# =========================================================
# CHAT
# =========================================================

st.title("💳 Credit Card Spend Summarizer")

st.caption(
    "Ask questions about your spending, rewards, "
    "international transactions, and fee waiver progress."
)


# ---------------------------------------------------------
# SUGGESTED QUESTIONS
# ---------------------------------------------------------

st.subheader("💡 Suggested Questions")

suggested_questions = [
    "What are the rewards on my credit card?",
    "What are the international transaction benefits?",
    "What is the fee waiver policy?",
    "What is the billing cycle for my card?",
]


col1, col2 = st.columns(2)

for index, question in enumerate(suggested_questions):

    target_col = (
        col1
        if index % 2 == 0
        else col2
    )

    with target_col:

        if st.button(
            question,
            key=f"suggested_{index}",
            use_container_width=True,
        ):

            st.session_state.selected_query = question

            st.rerun()


# ---------------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(
            message["content"]
        )


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

query = st.chat_input(
    "Ask about your credit card spending..."
)


# ---------------------------------------------------------
# SELECTED QUESTION
# ---------------------------------------------------------

if st.session_state.selected_query:

    query = st.session_state.selected_query

    st.session_state.selected_query = ""


# ---------------------------------------------------------
# SEND QUERY
# ---------------------------------------------------------

if query:

    # -----------------------------------------------------
    # USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )

    with st.chat_message("user"):

        st.markdown(query)

    # -----------------------------------------------------
    # ASSISTANT RESPONSE
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        placeholder = st.empty()

        placeholder.markdown("Thinking...")

        try:

            response = requests.post(
                STREAM_API_URL,
                json={
                    "query": query,
                    "thread_id": st.session_state.thread_id,
                    "chat_history": st.session_state.messages,
                    "role": st.session_state.role,
                    "username": st.session_state.username,
                },
                stream=True,
                timeout=120,
            )

            if response.status_code != 200:

                placeholder.empty()

                st.error(
                    f"API Error: {response.status_code}\n\n"
                    f"{response.text}"
                )

            else:

                answer = ""

                for chunk in response.iter_content(
                    chunk_size=None,
                    decode_unicode=True,
                ):

                    if chunk:

                        if not answer:
                            placeholder.empty()

                        answer += chunk

                        placeholder.markdown(
                            answer
                        )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

        except requests.exceptions.ConnectionError:

            placeholder.empty()

            st.error(
                "Cannot connect to FastAPI. "
                "Make sure the FastAPI server is running."
            )

        except requests.exceptions.Timeout:

            placeholder.empty()

            st.error(
                "The request timed out. "
                "Please try again."
            )

        except Exception as e:

            placeholder.empty()

            st.error(
                f"Unexpected error: {e}"
            )