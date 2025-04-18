import json
from typing import List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ClassData:
    package: str = ""
    id: str = ""
    type: str = "class"
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
        """Remove potential quotes for consistent ID checking."""
        if isinstance(node_id, str) and node_id.startswith('"') and node_id.endswith('"'):
            return node_id[1:-1]
        return node_id

    def add_blank_classes(self):
        # Normalize IDs before comparison
        defined_nodes = {self._normalize_id(node.id) for node in self.nodes}
        referenced_nodes = {self._normalize_id(link.source) for link in self.links}.union(
            {self._normalize_id(link.target) for link in self.links}
        )

        undefined_nodes = referenced_nodes - defined_nodes

        for undefined_node_id in undefined_nodes:
            # Add with the original ID (might be quoted)
            original_id = undefined_node_id  # Keep original form for adding
            if undefined_node_id not in defined_nodes:  # Check again just in case
                print(f"Adding blank node for undefined reference: {undefined_node_id}")
                blank_node = ClassData(
                    id=undefined_node_id,  # Use the ID as found in links
                    attributes=[],
                    methods=[],
                    linesOfCode=None,
                    complexity=None,
                    module=None,
                )
                self.nodes.append(blank_node)

    def remove_duplicates(self):
        # Remove duplicate nodes based on normalized 'id'
        unique_nodes = {}
        kept_nodes = []
        for node in self.nodes:
            node_id_normalized = self._normalize_id(node.id)
            if node_id_normalized not in unique_nodes:
                unique_nodes[node_id_normalized] = node
                kept_nodes.append(node)
            else:
                # Optional: Merge data if duplicates found, or just keep first
                print(f"Duplicate node found and removed: {node.id} (normalized: {node_id_normalized})")
        self.nodes = kept_nodes

        # Remove duplicate links based on normalized 'source', 'target', 'relation'
        unique_links = set()
        filtered_links = []
        for link in self.links:
            link_id_tuple = (
                self._normalize_id(link.source),
                self._normalize_id(link.target),
                link.relation
            )
            if link_id_tuple not in unique_links:
                unique_links.add(link_id_tuple)
                filtered_links.append(link)
            else:
                print(f"Duplicate link found and removed: {link.source} -> {link.target} ({link.relation})")
        self.links = filtered_links

    def to_json(self) -> str:
        # Duplicates should be removed before calling this
        # Blank classes should be added before calling this
        # Ensure nodes/links are stable before dumping
        self.nodes.sort(key=lambda x: self._normalize_id(x.id))
        self.links.sort(key=lambda x: (self._normalize_id(x.source), self._normalize_id(x.target), x.relation))
        return json.dumps(asdict(self), indent=4)
