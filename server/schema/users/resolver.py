from ariadne import QueryType, MutationType
from bson import ObjectId
from server.models.user_model import UpdateUserModel
from server.helpers.mongo_helper import MongoHelper
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper


class UserResolver:
    def __init__(self):
        self.query = QueryType()
        self.mutation = MutationType()
        self.__mongo_helper = MongoHelper(allowed_collections=["users"])
        self._bind_queries()
        self._bind_mutations()

    def _bind_queries(self):
        self.query.set_field("users", self.resolve_users)
        self.query.set_field("user", self.resolve_user)

    def _bind_mutations(self):
        self.mutation.set_field("updateUser", self.resolve_update_user)
        self.mutation.set_field("deleteUser", self.resolve_delete_user)

    def user_to_dict(self, user):
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "isAdmin": user.get("isAdmin", False),
        }

    def resolve_users(self, _, info):
        users = self.__mongo_helper.find_many("users", {})
        return [self.user_to_dict(user) for user in users]

    def resolve_user(self, _, info, id):
        user = self.__mongo_helper.find_one("users", {"_id": ObjectId(id)})
        if not user:
            return None
        return self.user_to_dict(user)

    def resolve_update_user(self, _, info, input):
        user_id = ObjectId(input["id"])
        model = UpdateUserModel(**input)
        update_data = model.model_dump(exclude_unset=True)

        user = self.__mongo_helper.find_one("users", {"_id": user_id})
        if not user:
            raise CustomGraphQLExceptionHelper("Usuario no encontrado")
        if update_data:
            self.__mongo_helper.update_one(
                "users", {"_id": user_id}, {"$set": update_data}
            )

        user = self.__mongo_helper.find_one("users", {"_id": user_id})
        return self.user_to_dict(user)

    def resolve_delete_user(self, _, info, id):
        result = self.__mongo_helper.delete_one("users", {"_id": ObjectId(id)})
        return result["deleted_count"] == 1

    def get_resolvers(self):
        return [self.query, self.mutation]
