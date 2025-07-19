from ariadne import load_schema_from_path, make_executable_schema
from pathlib import Path

from .hello.resolvers import resolvers as hello_resolvers

schemas_path = Path(__file__).parent

# Cargar todos los archivos .graphql
type_defs = "\n".join(
    [
        load_schema_from_path(schemas_path / "hello/schema.graphql"),
    ]
)

# Unir todos los resolvers
all_resolvers = []
all_resolvers.extend(hello_resolvers)

schema = make_executable_schema(type_defs, *all_resolvers)
