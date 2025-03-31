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

    def add_blank_classes(self):
        defined_nodes = {node.id for node in self.nodes}
        referenced_nodes = {link.source for link in self.links}.union(
            {link.target for link in self.links}
        )

        undefined_nodes = referenced_nodes - defined_nodes

        for undefined_node in undefined_nodes:
            blank_node = ClassData(
                id=undefined_node,
                attributes=[],
                methods=[],
                linesOfCode=None,
                complexity=None,
                module=None,
            )
            self.nodes.append(blank_node)

    def remove_duplicates(self):
        # Remove duplicate nodes explicitly based on 'id'
        unique_nodes = {}
        for node in self.nodes:
            node_id = node.id
            if node_id not in unique_nodes:
                unique_nodes[node_id] = node
        self.nodes = list(unique_nodes.values())

        # Remove duplicate links explicitly based on 'source', 'target', 'relation'
        unique_links = set()
        filtered_links = []
        for link in self.links:
            link_id = (link.source, link.target, link.relation)
            if link_id not in unique_links:
                unique_links.add(link_id)
                filtered_links.append(link)
        self.links = filtered_links

    def to_json(self) -> str:
        # Ensure duplicates are explicitly removed before converting to JSON
        self.remove_duplicates()
        self.add_blank_classes()
        return json.dumps(asdict(self), indent=4)
