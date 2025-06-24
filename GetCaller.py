from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import re
from langchain.prompts import PromptTemplate
from langchain_neo4j import  Neo4jGraph
from dotenv import load_dotenv
from pydantic import BaseModel , Field
from typing import List

load_dotenv()

graph = Neo4jGraph()


class Caller(BaseModel):
    name: str
    file: str
    code: str

class CypherResult(BaseModel):
    target_name: str = Field(..., description="Name of the target function")
    target_file: str = Field(..., description="File where the function is defined")
    target_code: str = Field(..., description="Source code of the function")
    callers: List[Caller] = Field(..., description="List of caller functions")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
)

KG_SCHEMA = """
You are working with a Neo4j knowledge graph with the following structure:

Node Types:
- Function {name, code}
- File {name}
- Class {name}

Relationships:
- (Function)-[:DEFINED_IN]->(File)
- (Function)-[:Call]->(Function)
- (Function)<-[:USED_IN]-(Function)
- (Class)-[:DEFINED_IN]->(File)
- (Class)-[:INHERITS_FROM]->(Class)

Each Function node has:
- `name`: the function name
- `code`: the function's full source code

Each function is connected to the file it is defined in via:
- (Function)-[:DEFINED_IN]->(File)

Functions can call each other via:
- (caller:Function)-[:Call]->(callee:Function)

---

You will be asked natural language questions. Your task is to **only generate valid Cypher queries** that return:

1. The function being queried (callee):  
   - its name  
   - the file it's defined in  
   - its source code

2. All caller functions (those that call the above function):  
   - each caller's name  
   - the file it is defined in  
   - its source code

---

Use this Cypher template:

```cypher
MATCH (callee:Function {name: "func_name"})-[:DEFINED_IN]->(calleeFile:File)
OPTIONAL MATCH (caller:Function)-[:Call]->(callee)
OPTIONAL MATCH (caller)-[:DEFINED_IN]->(callerFile:File)
RETURN
  callee.name AS target_name,
  calleeFile.name AS target_file,
  callee.code AS target_code,
  collect({name: caller.name, file: callerFile.name, code: caller.code}) AS callers
"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template="""
{schema}

Question: {question}

Cypher:
"""
)

def generate_cypher_query(user_question):
    full_prompt = cypher_prompt.format(schema=KG_SCHEMA, question=user_question)
    result = llm.invoke([HumanMessage(content=full_prompt)])
    
    match = re.search(r"```cypher(.*?)```", result.content, re.DOTALL)
    cypher = match.group(1).strip() if match else result.content.strip()
    return cypher

# 📡 Run Query and Validate with Pydantic
def run_query(cypher_query):
    try:
        result = graph.query(cypher_query)
        if not result or not isinstance(result, list) or not result[0]:
            return {"error": "Empty or invalid query result"}
        validated_result = CypherResult(**result[0])
        return [validated_result.dict()]
    except Exception as e:
        return {"error": str(e)}


