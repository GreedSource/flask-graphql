from ariadne import load_schema_from_path, make_executable_schema
from pathlib import Path

from .hello.resolver import HelloResolver
from .users.resolver import UserResolver
from .auth.resolver import AuthResolver

__user_resolver = UserResolver()
__hello_resolver = HelloResolver()
__auth_resolver = AuthResolver()

schemas_path = Path(__file__).parent

# Cargar todos los archivos .graphql
# Carga TODOS los .graphql del folder schema/
type_defs = load_schema_from_path(schemas_path)  # o la carpeta que tengas

# Unir todos los resolvers
all_resolvers = []
all_resolvers.extend(__hello_resolver.get_resolvers())
all_resolvers.extend(__user_resolver.get_resolvers())
all_resolvers.extend(__auth_resolver.get_resolvers())

schema = make_executable_schema(type_defs, *all_resolvers)
