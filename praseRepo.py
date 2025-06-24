import ast, os, json, textwrap
from collections import defaultdict

RELATIONS = {
    "functions": {},            # function_name -> file
    "function_code": {},        # function_name -> full source code
    "classes": {},              # class_name -> {file, bases}
    "function_calls": defaultdict(list),  # funcA -> [funcB, funcC]
    "imports": defaultdict(list),         # file.py -> [imported_module_or_function]
    "class_inheritance": defaultdict(list) # classA -> [base1, base2]
}

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, filename, source_lines):
        self.filename = filename
        self.source_lines = source_lines
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node):
        full_func_name = f"{self.current_class + '.' if self.current_class else ''}{node.name}"

        RELATIONS["functions"][full_func_name] = self.filename

        func_code = textwrap.dedent("".join(self.source_lines[node.lineno - 1 : node.end_lineno]))
        RELATIONS["function_code"][full_func_name] = func_code

        prev_func = self.current_function
        self.current_function = full_func_name
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_ClassDef(self, node):
        RELATIONS["classes"][node.name] = {
            "file": self.filename,
            "bases": [b.id for b in node.bases if isinstance(b, ast.Name)]
        }
        RELATIONS["class_inheritance"][node.name].extend(RELATIONS["classes"][node.name]["bases"])
        prev_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = prev_class

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        else:
            callee = "<unknown>"
        if self.current_function:
            RELATIONS["function_calls"][self.current_function].append(callee)
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            RELATIONS["imports"][self.filename].append(a.name)

    def visit_ImportFrom(self, node):
        module = node.module
        for a in node.names:
            full_name = f"{module}.{a.name}" if module else a.name
            RELATIONS["imports"][self.filename].append(full_name)

def crawl_repo(repo_path):
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source_lines = f.readlines()
                        tree = ast.parse("".join(source_lines), filename=file)
                        analyzer = CodeAnalyzer(file, source_lines)
                        analyzer.visit(tree)
                except Exception as e:
                    print(f"Error parsing {file}: {e}")


def extractRelation(repo_path):
    crawl_repo(repo_path)

    with open("relations.json", "w", encoding="utf-8") as f:
        json.dump(RELATIONS, f, indent=2, ensure_ascii=False)

    print("Done. Results saved to relations.json")
