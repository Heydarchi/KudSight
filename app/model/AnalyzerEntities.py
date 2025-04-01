from dataclasses import dataclass, field
from typing import List
from enum import Enum


class InheritanceEnum(Enum):
    EXTENDED = 1
    IMPLEMENTED = 2
    DEPENDED = 3


class AccessEnum(Enum):
    PUBLIC = 1
    PRIVATE = 2
    PROTECTED = 3


@dataclass
class VariableNode:
    name: str = ""
    dataType: str = ""
    accessLevel: AccessEnum = AccessEnum.PUBLIC
    isStatic: bool = False
    isFinal: bool = False


@dataclass
class MethodNode:
    name: str = ""
    dataType: str = ""
    accessLevel: AccessEnum = AccessEnum.PUBLIC
    params: List[str] = field(default_factory=list)
    isStatic: bool = False
    isOverridden: bool = False
    variables: List[VariableNode] = field(default_factory=list)


@dataclass
class Inheritance:
    name: str
    relationship: InheritanceEnum


@dataclass
class UmlRelationMap:
    name: str = ""
    relationship: InheritanceEnum = InheritanceEnum.DEPENDED


@dataclass
class ClassNode:
    package: str = ""
    name: str = ""
    accessLevel: AccessEnum = AccessEnum.PUBLIC
    isStatic: bool = False
    isFinal: bool = False
    isInterface: bool = False
    variables: List[VariableNode] = field(default_factory=list)
    methods: List[MethodNode] = field(default_factory=list)
    relations: List[Inheritance] = field(default_factory=list)
    classes: List["ClassNode"] = field(default_factory=list)


class FileTypeEnum(Enum):
    UNDEFINED = 0
    C = 1
    CPP = 2
    JAVA = 3
    KOTLIN = 4
    PYTHON = 5
    CSHARP = 6
