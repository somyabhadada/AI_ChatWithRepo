import os
import ast
from typing import List
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import shutil  

def extract_functions_and_classes_from_code(code: str, file_path: str, module: str) -> List[Document]:
    tree = ast.parse(code)
    lines = code.splitlines()
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            start_line = node.lineno - 1
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
            source = "\n".join(lines[start_line:end_line])
            name = node.name
            kind = "function" if isinstance(node, ast.FunctionDef) else "class"
      
            enriched_content = f"{kind} `{name}` in module `{module}`:\n\n{source}"
            doc = Document(
                page_content=enriched_content,
                metadata={
                    "name": name,
                    "type": kind,
                    "file": os.path.basename(file_path),
                    "module": module,
                    "start_line": start_line + 1,
                    "end_line": end_line
                }
            )
            chunks.append(doc)

    return chunks

def path_to_module(repo_root: str, file_path: str) -> str:
    rel_path = os.path.relpath(file_path, repo_root)
    no_ext = os.path.splitext(rel_path)[0]
    return no_ext.replace(os.sep, ".")

def crawl_repo(repo_path: str) -> List[Document]:
    all_doc = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        code = f.read()
                        module = path_to_module(repo_path, full_path)
                        all_doc.extend(extract_functions_and_classes_from_code(code, full_path, module))
                except Exception as e:
                    print(f" Error parsing {file}: {e}")
    return all_doc


def buildDB(repo_path):
    repo_name = os.path.basename(os.path.normpath(repo_path))  
    persist_path = os.path.join("vector_db", repo_name)

    embedding_model = HuggingFaceEmbeddings(
        model_name="bge-code-v1",
        model_kwargs={"device": "cpu"}
    )

    documents = crawl_repo(repo_path)
    

    vectordb = Chroma.from_documents(
        documents,
        embedding=embedding_model,
        persist_directory=persist_path
    )

    vectordb.persist()
    print(f"Extracted {len(documents)} documents.")
    return persist_path
