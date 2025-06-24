from langchain.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainFilter 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from dotenv import load_dotenv
from langchain.chains import LLMChain

load_dotenv()


embedding_model = HuggingFaceEmbeddings(
    model_name="bge-code-v1",  
    model_kwargs={"device": "cpu"}
)

from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["history", "query", "context"],
    template="""
You are a highly intelligent GitHub assistant.

Conversation so far:
{history}

Relevant code context from the repository:
{context}

User question:
{query}

---

Instructions:
1. Begin with a direct answer.
2. Then provide a detailed explanation using specific references to function names and file/modules (e.g., `auth.routes`, `auth.utils`).
3. Use code blocks where helpful.
4. If the feature is missing, respond: "There is no such feature implemented in this repo."
5. Suggest implementation ideas if possible.
6. Use clear, structured formatting (markdown-friendly).

Your Answer:
"""
)

def github_assistant_chat(query: str , memory , path):
    vectordb = Chroma(
    persist_directory = path,
    embedding_function=embedding_model
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        disable_streaming=False,
        callbacks=[StreamingStdOutCallbackHandler()],                    
    )

    base_retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "lambda_mult": 0.7
        }
    )

    multi_query_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
    )

    compressor = LLMChainFilter.from_llm(llm) 

    combined_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=multi_query_retriever
    )

    docs = combined_retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in docs])

    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
    )

    response = chain.run({
        "query": query,
        "context": context
    })

    return response
