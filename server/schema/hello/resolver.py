from ariadne import QueryType


class HelloResolver:
    def __init__(self):
        self.__query = QueryType()
        self._bind_queries()

    def _bind_queries(self):
        self.__query.set_field("hello", self.resolve_hello)

    def resolve_hello(_, info):
        return "¡Hola desde Ariadne!"

    def get_resolvers(self):
        return [self.__query]
