from langchain_neo4j import  Neo4jGraph
from dotenv import load_dotenv

load_dotenv()

graph = Neo4jGraph()


import json

with open("./relations.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def buildGraph():
    query_delete_all = """
    MATCH (n)
    DETACH DELETE (n)
    """
    graph.query(query=query_delete_all)

    query = """
    MERGE (f:Function {name: $fun_name})
    SET f.code = $fun_code
    MERGE (fi:File {name: $file_name})
    MERGE (f)-[:DEFINED_IN]->(fi)
    """

    for x in data['functions']:
        graph.query(query=query , params={
            "fun_name" : x,
            "file_name" : data['functions'][x],
            "fun_code" : data['function_code'][x],
        })

    query_funCall = """
    MERGE (f:Function {name: $Caller})
    MERGE (fi:Function {name: $Calle})
    MERGE (f)-[:Call]->(fi)
    """
    for x in data['function_calls']:
        for y in data['function_calls'][x]:
            graph.query(query=query_funCall , params={
                "Caller" : x,
                "Calle" : y
            })

    query_funCallie = """
    MERGE (f:Function {name: $Caller})
    MERGE (fi:Function {name: $Calle})
    MERGE (fi)-[:USED_IN]->(f)
    """
    node_count = 0
    for x in data['function_calls']:
        for y in data['function_calls'][x]:
            graph.query(query=query_funCallie , params={
                "Caller" : x,
                "Calle" : y
            })
            print("Realtion Created successFully" , node_count)
            node_count+=1


    query_Class = """
    MERGE (f:Class {name: $Class})
    MERGE (fi:File {name: $file_name})
    MERGE (f)-[:DEFINED_IN]->(fi)
    """
    for x in data['classes']:
        graph.query(query=query_Class , params={
            "Class" : x,
            "file_name" : data['classes'][x]['file']
        })


    query_Class_In = """
    MERGE (f:Class {name: $Class})
    MERGE (c:Class {name: $Base})
    MERGE (f)-[:INHERITS_FROM]->(c)
    """
    for x in data['classes']:
        for y in data['classes'][x]['bases']:
          graph.query(query=query_Class_In , params={
            "Class" : x,
            "Base" : y
          })
