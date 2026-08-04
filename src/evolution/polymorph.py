import ast
import random
import logging
from pathlib import Path

class ASTPolymorpher(ast.NodeTransformer):
    """Injeta variáveis de entropia (código morto) para mutação determinística."""
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        
        salt_val = random.randint(1000000, 9999999)
        dead_node = ast.Assign(
            targets=[ast.Name(id='_aion_entropy_salt', ctx=ast.Store())],
            value=ast.Constant(value=salt_val)
        )
        
        insert_idx = 0
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
            insert_idx = 1
            
        node.body.insert(insert_idx, dead_node)
        return node

def apply_polymorphism(filepath: Path) -> bool:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
        transformer = ASTPolymorpher()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        new_source = ast.unparse(new_tree)
        filepath.write_text(new_source, encoding="utf-8")
        return True
    except Exception as e:
        logging.error(f"Polymorphism failed on {filepath}: {e}")
        return False

def polymorph_system(project_root: Path) -> Path | None:
    """Modifica a estrutura AST de um arquivo core do AION aleatoriamente."""
    # Para não quebrar o sistema inteiro num MVP, focaremos no executor
    targets = list((project_root / "src" / "executor").glob("*.py"))
    if targets:
        target = random.choice(targets)
        if apply_polymorphism(target):
            logging.warning(f"AST Polymorphism applied to {target.name}. Binary hash altered.")
            return target
    return None
