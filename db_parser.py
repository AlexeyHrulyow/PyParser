from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None

@dataclass
class ForeignKey:
    name: Optional[str]
    columns: list[str]
    ref_schema: str
    ref_table: str
    ref_columns: list[str]
    on_delete: Optional[str] = None
    on_update: Optional[str] = None

@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    uniques: list[list[str]] = field(default_factory=list)
    checks: list[str] = field(default_facory=list)

@dataclass
class Schema:
    name: str
    tables: dict[str,Table] = field(defult_factory = dict)

@dataclass
class DatabaseSchema:
    name: str = ""
    schemas: dict[str, Schema] = field(default_factory=dict)

class Provider:
    def fetch(self) -> DatabaseSchema:
        raise NotImplementedError

def format_tree(db: DatabaseSchema) -> str:
