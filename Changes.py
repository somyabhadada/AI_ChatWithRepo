from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from GetCaller import generate_cypher_query , run_query
from langchain.chains import LLMChain

prompt = PromptTemplate(
    input_variables=['query' , 'func_code' , 'fun_loc', 'caller_code'],

    template=""" 
    You are strong Python developer who will assist user to do changes based on there question you are provided current function code and other functions which call 
    this function modify the function based on user question  also modify dependent functions if needed !
    User : {query},
    function_code : {func_code}
    function_defined in : {fun_loc}
    Caller's code : {caller_code}
"""
)

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.0-flash",
    temperature = 0.5
)

def format_callers(callers):
    return "\n\n".join(
        f"# {c['name']} (in {c['file']})\n```python\n{c['code']}\n```"
        for c in callers
    )

def changeResults(user_input , memory):
    cypher = generate_cypher_query(user_input)

    result = run_query(cypher)
    formatted_callers = format_callers(result[0]["callers"])

    chain = LLMChain(llm=llm, prompt=prompt, memory=memory)

    response = chain.run({
        "query": user_input,
        "func_code": result[0]["target_code"],
        "fun_loc": result[0]["target_file"],
        "caller_code": formatted_callers
    })

    return response
