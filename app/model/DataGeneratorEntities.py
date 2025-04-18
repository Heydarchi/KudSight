import json
from typing import List, Optional

# Add FileTypeEnum import
from model.AnalyzerEntities import FileTypeEnum
from dataclasses import dataclass, field, asdict, fields


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
    analysisSourcePath: Optional[str] = None
    # Add language context storage
    _language_context: FileTypeEnum = field(
        default=FileTypeEnum.UNDEFINED, compare=False, repr=False
    )

    def _normalize_id(self, node_id: str) -> str:
        """Return the ID as is. Assumes IDs are consistently generated qualified names."""
        return node_id if isinstance(node_id, str) else ""

    # Modify add_blank_classes to use the stored language context
    def add_blank_classes(self):
        defined_nodes_raw = {node.id for node in self.nodes}
        referenced_nodes = {link.source for link in self.links}.union(
            {link.target for link in self.links}
        )
        undefined_nodes = referenced_nodes - defined_nodes_raw

        # Determine separator based on stored language context
        separator = "." if self._language_context == FileTypeEnum.JAVA else "::"

        for undefined_node_id in undefined_nodes:
            if undefined_node_id and undefined_node_id not in defined_nodes_raw:
                package_guess = ""
                simple_id_guess = undefined_node_id

                # Attempt package extraction only if the expected separator is present
                if separator in undefined_node_id:
                    parts = undefined_node_id.rsplit(
                        separator, 1
                    )  # Split only once from the right
                    if len(parts) == 2:
                        package_guess = parts[0]
                        simple_id_guess = parts[1]
                    # else: it contains the separator but not in a way that suggests a package (e.g., starts with it?)

                blank_node = ClassData(
                    id=undefined_node_id,
                    package=package_guess,  # Use the guessed package
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
        self.links = filtered_links

    def to_json(self) -> str:
        # Sort nodes and links before converting to dict
        self.nodes.sort(key=lambda x: x.id)
        self.links.sort(key=lambda x: (x.source, x.target, x.relation))

        # Convert the entire dataclass instance (including nested ones) to a dictionary
        data_dict = asdict(self)

        # Remove the internal _language_context field from the top-level dictionary
        if "_language_context" in data_dict:
            del data_dict["_language_context"]

        # Now serialize the dictionary which contains only JSON-compatible types
        return json.dumps(data_dict, indent=4)
