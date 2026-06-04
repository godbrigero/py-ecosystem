from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from typing import Iterator

from grimp import ImportGraph

from importlinter.application import output
from importlinter.domain.contract import Contract, ContractCheck


class RelativeOnlyContract(Contract):
    """
    Require relative imports for all internal references within root_package.

    Absolute imports like ``from ecosystem.foo import bar`` break when the package
    is vendored without being installed as a top-level package.
    """

    def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
        root_package = self._root_package()
        violations = list(_find_absolute_internal_imports(root_package))
        return ContractCheck(kept=not violations, metadata={"violations": violations})

    def render_broken_contract(self, check: ContractCheck) -> None:
        for violation in check.metadata["violations"]:
            output.print(
                f"{violation['file']}:{violation['line']}: "
                f"absolute import of '{violation['module']}' — "
                f"use a relative import (e.g. from .{violation['suffix']} import ...)"
            )

    def _root_package(self) -> str:
        if "root_package" in self.session_options:
            return self.session_options["root_package"]
        root_packages = self.session_options.get("root_packages", [])
        if len(root_packages) == 1:
            return root_packages[0]
        raise ValueError("relative_only contract requires a single root_package.")


def _package_directory(root_package: str) -> Path:
    spec = importlib.util.find_spec(root_package)
    if spec is None:
        raise ValueError(f"Could not import root package '{root_package}'.")
    if spec.submodule_search_locations:
        return Path(spec.submodule_search_locations[0])
    if spec.origin:
        return Path(spec.origin).parent
    raise ValueError(f"Could not locate files for package '{root_package}'.")


def _find_absolute_internal_imports(root_package: str) -> Iterator[dict[str, str | int]]:
    package_dir = _package_directory(root_package)
    prefix = f"{root_package}."

    for path in sorted(package_dir.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level != 0 or not node.module:
                    continue
                if node.module == root_package or node.module.startswith(prefix):
                    yield _violation(path, node.lineno, node.module, root_package)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == root_package or alias.name.startswith(prefix):
                        yield _violation(path, node.lineno, alias.name, root_package)


def _violation(
    path: Path, lineno: int, module: str, root_package: str
) -> dict[str, str | int]:
    suffix = module.removeprefix(f"{root_package}.")
    return {
        "file": str(path),
        "line": lineno,
        "module": module,
        "suffix": suffix,
    }
