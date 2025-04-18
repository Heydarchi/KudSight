import json
from typing import List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ClassData:
    package: str = ""
    id: str = ""
    type: str = "class"
    isAbstract: bool = False
    isFinal: bool = False
    isStatic: bool = False
    attributes: Optional[List[str]] = field(default_factory=list)
    methods: Optional[List[str]] = field(default_factory=list)
    linesOfCode: Optional[int] = None
    complexity: Optional[str] = None
    module: Optional[str] = None


@dataclass
class ModuleData:
    id: str = ""
    type: str = "module"
    version: Optional[str] = None
    linesOfCode: Optional[int] = None
    classes: Optional[List[str]] = field(default_factory=list)


@dataclass
class Dependency:
    source: str = ""
    target: str = ""
    relation: str = ""


@dataclass
class GraphData:
    nodes: List = field(default_factory=list)
    links: List = field(default_factory=list)

    def _normalize_id(self, node_id: str) -> str:
        """Return the ID as is. Assumes IDs are consistently generated qualified names."""
        return node_id if isinstance(node_id, str) else ""

    def add_blank_classes(self):
        # Use raw IDs (qualified names) for checking
        defined_nodes = {node.id for node in self.nodes}
        referenced_nodes = {link.source for link in self.links}.union(
            {link.target for link in self.links}
        )

        undefined_nodes = referenced_nodes - defined_nodes
        # Normalize IDs before comparison # This comment seems misplaced from previous logic, but harmless
        defined_nodes = {
            self._normalize_id(node.id) for node in self.nodes
        }  # This re-calculates defined_nodes using normalized ID, which contradicts the goal of using raw IDs. Let's fix this too.
        # --- Start Change: Use raw IDs for checking existence ---
        defined_nodes_raw = {
            node.id for node in self.nodes
        }  # Use raw IDs for the check
        # --- End Change ---
        for undefined_node_id in undefined_nodes:
            # --- Start Change: Check against raw defined IDs ---
            if (
                undefined_node_id and undefined_node_id not in defined_nodes_raw
            ):  # Check against raw IDs
                # --- End Change ---
                print(f"Adding blank node for undefined reference: {undefined_node_id}")
                # Extract package and simple ID heuristically if possible, otherwise leave package blank
                package_guess = ""
                simple_id_guess = undefined_node_id
                if "::" in undefined_node_id:
                    parts = undefined_node_id.split("::")
                    package_guess = "::".join(parts[:-1])
                    simple_id_guess = parts[-1]

                blank_node = ClassData(
                    id=undefined_node_id,  # Use the qualified name as the ID
                    package=package_guess,  # Best guess for package
                    attributes=[],
                    methods=[],
                    linesOfCode=None,
                    complexity=None,
                    module=None,
                )
                self.nodes.append(blank_node)

    def remove_duplicates(self):
        # Remove duplicate nodes based on the raw 'id' (qualified name)
        unique_nodes = {}
        kept_nodes = []
        for node in self.nodes:
            node_id = node.id  # Use raw ID
            if node_id not in unique_nodes:
                unique_nodes[node_id] = node
                kept_nodes.append(node)
            else:
                print(f"Duplicate node found and removed: {node.id}")
        self.nodes = kept_nodes

        # Remove duplicate links based on raw 'source', 'target', 'relation'
        unique_links = set()
        filtered_links = []
        for link in self.links:
            link_id_tuple = (
                link.source,  # Use raw ID
                link.target,  # Use raw ID
                link.relation,
            )
            if link_id_tuple not in unique_links:
                unique_links.add(link_id_tuple)
                filtered_links.append(link)
            else:
                print(
                    f"Duplicate link found and removed: {link.source} -> {link.target} ({link.relation})"
                )
        self.links = filtered_links

    def to_json(self) -> str:
        # Sort using raw ID
        self.nodes.sort(key=lambda x: x.id)
        self.links.sort(key=lambda x: (x.source, x.target, x.relation))
        return json.dumps(asdict(self), indent=4)
