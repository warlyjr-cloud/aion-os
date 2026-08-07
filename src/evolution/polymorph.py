import ast
import logging
import random
from pathlib import Path
from typing import Any, cast

from evolution.schrodinger import SchrodingerExecutor


class ASTPolymorpher(ast.NodeTransformer):
    """Injeta variáveis de entropia (código morto) para mutação determinística."""

    def __init__(self, salt_length: int = 8):
        self.salt_length = salt_length

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)

        salt_val = "".join(
            random.choices(  # noqa: S311 - dead-code marker, not a secret/credential
                "abcdefghijklmnopqrstuvwxyz0123456789", k=self.salt_length
            )
        )
        dead_node = ast.Assign(
            targets=[ast.Name(id="_aion_entropy_salt", ctx=ast.Store())],
            value=ast.Constant(value=salt_val),
        )

        insert_idx = 0
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        ):
            insert_idx = 1

        node.body.insert(insert_idx, dead_node)
        return node


def apply_polymorphism(project_root: Path) -> bool:
    python_files = list((project_root / "src" / "executor").glob("*.py"))

    if not python_files:
        logging.info("[\ud83e\uddec POLYMORPH] No Python files to mutate.")
        return False

    target_file = random.choice(python_files)  # noqa: S311 - picking a demo target, not security

    # Run the mutation in Quantum Superposition (3 dimensions)
    # We test 3 different random salt lengths. The first one that compiles
    # and parses successfully wins.
    scheduler = SchrodingerExecutor(dimensions=3)

    # Wrapper function for the superposition execution
    def _attempt_mutation(salt_length: int) -> bool:
        original_code = target_file.read_text(encoding="utf-8")
        tree = ast.parse(original_code)

        mutator = ASTPolymorpher(salt_length=salt_length)
        mutated_tree = mutator.visit(tree)
        ast.fix_missing_locations(mutated_tree)

        mutated_code = ast.unparse(mutated_tree)

        if not mutated_code.strip():
            raise ValueError("generated mutated code is empty")

        # Verify it compiles
        compile(mutated_code, target_file.name, "exec")

        # If it passes, save it
        target_file.write_text(mutated_code, encoding="utf-8")
        logging.info(
            f"[\ud83e\uddec POLYMORPH] Superposition collapsed: Mutated {target_file.name} "
            f"with salt length {salt_length}."
        )
        return True

    try:
        # We pass 3 different realities (salt lengths) to test simultaneously
        return cast(Any, scheduler).execute_in_superposition(_attempt_mutation, [(4,), (8,), (12,)])
    except RuntimeError:
        logging.error("[\ud83e\uddec POLYMORPH] Mutation failed in all quantum realities.")
        return False


def polymorph_system(project_root: Path) -> Path | None:
    """Modifica a estrutura AST de um arquivo core do AION em Superposição Quântica."""
    if apply_polymorphism(project_root):
        logging.warning(
            "[\ud83e\uddec POLYMORPH] AST Polymorphism applied. "
            "Binary hash altered across dimensions."
        )
        # Return dummy path as indicator of success
        return project_root
    return None
