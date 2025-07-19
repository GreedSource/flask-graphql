from ariadne import load_schema_from_path, make_executable_schema
from pathlib import Path

from .hello.resolvers import resolvers as hello_resolvers
from .users.resolvers import resolvers as users_resolvers


schemas_path = Path(__file__).parent

# Cargar todos los archivos .graphql
# Carga TODOS los .graphql del folder schema/
type_defs = load_schema_from_path(schemas_path)  # o la carpeta que tengas

# Unir todos los resolvers
all_resolvers = []
all_resolvers.extend(hello_resolvers)
all_resolvers.extend(users_resolvers)

schema = make_executable_schema(type_defs, *all_resolvers)
