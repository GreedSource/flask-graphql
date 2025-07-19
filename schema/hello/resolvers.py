from ariadne import QueryType

query = QueryType()


@query.field("hello")
def resolve_hello(_, info):
    return "¡Hola desde Ariadne!"


resolvers = [query]
