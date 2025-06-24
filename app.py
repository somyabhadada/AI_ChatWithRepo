import os
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationSummaryMemory

from main import handle_query
from BuildKG import buildGraph
from cloneRepo import clone_repo
from praseRepo import extractRelation
from VectorDB import buildDB

load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3
)

# Setup memory
if "memory" not in st.session_state:
    st.session_state.memory = ConversationSummaryMemory(
        llm=llm,
        memory_key="history",
        input_key="query"
    )

# Setup chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Page settings
st.set_page_config(page_title="GitHub AI Assistant", page_icon="🤖")
st.title("🤖 GitHub Code Assistant")

# Repo setup
if "repo_processed" not in st.session_state:
    st.session_state.repo_processed = False

if not st.session_state.repo_processed:
    repo_url = st.text_input("🔗 Enter GitHub Repository URL:")

    if repo_url:
        with st.spinner("🔄 Cloning the repository..."):
            try:
                repo_name = repo_url.rstrip("/").split("/")[-1]
                repo_path = os.path.join("cloned_repos", repo_name)

                # Clone the repo
                clone_repo(repo_url, repo_path)

                # Build vector DB, extract relations, build KG
                print("🚧 Start building DB")
                vector_path = buildDB(repo_path)
                print("✅ Done building DB")

                extractRelation(repo_path)
                buildGraph()

                # Store in session state
                st.session_state.repo_processed = True
                st.session_state.repo_path = repo_path
                st.session_state.vector_path = vector_path

                st.success("✅ Repository processed successfully!")

            except Exception as e:
                st.error(f"❌ Failed to process repo: {e}")
                st.stop()

# Chat interface
if st.session_state.repo_processed:
    user_query = st.chat_input("💬 Ask something about the repo...")

    if user_query:
        with st.spinner("🤔 Thinking..."):
            response = handle_query(
                user_query,
                st.session_state.memory,
                st.session_state.vector_path
            )
            st.session_state.chat_history.append(("user", user_query))
            st.session_state.chat_history.append(("assistant", response))

    for sender, message in st.session_state.chat_history:
        if sender == "user":
            st.chat_message("user").markdown(message)
        else:
            st.chat_message("assistant").markdown(message)
