from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationSummaryMemory
from langchain.chains import LLMChain
from Changes import changeResults
from RetriverBot import github_assistant_chat 

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3
)

memory = ConversationSummaryMemory(
    llm=llm,
    memory_key="history",
    input_key="query"
)

# 2. Router Chain
router_prompt = PromptTemplate(
    input_variables=["query", "history"],
    template="""
You are a smart router.

Here is the previous conversation history:
{history}

Now, classify the user's current query into one of the following categories:
- "memory" if the query is a follow-up, clarification, or general question not needing code.
- "retrieval" if the query is about understanding the codebase (e.g., how something works).
- "edit" if the query suggests a change to the codebase or asks how to implement a feature.
- "create" if the user wants to create a new file (e.g., "create a new utils.py", "add a new route file", "make a model").

Query: {query}
Answer:
"""

)


def create_file_from_query(query: str) -> str:
    
    prompt = PromptTemplate(
        input_variables=["query"],
        template="""
        You are a code assistant.

        Based on the user's request, generate a file name and the complete code content.

        user : {query}
        """
    )

    chain = prompt | llm
    reponse  = chain.run({"query" : query})
    return reponse


router_chain = LLMChain(llm=llm, prompt=router_prompt)

def handle_query(query: str, memory, path: str):
    history_text = memory.load_memory_variables({})["history"]

    route = router_chain.run({
        "query": query,
        "history": history_text
    }).strip().lower()

    if route == "memory":
        memory_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["query", "history"],
                template="Conversation so far:\n{history}\n\nUser asked:\n{query}\n\nRespond appropriately:"
            ),
            memory=memory
        )
        return memory_chain.run({"query": query, "history": history_text})

    elif route == "retrieval":
        return github_assistant_chat(query, memory, path)

    elif route == "edit":
        return changeResults(query, memory)

    elif route == "create":
        return create_file_from_query(query)

    else:
        return "Sorry, I couldn't determine how to handle your query."
