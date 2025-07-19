from ariadne import QueryType, MutationType
from bson.objectid import ObjectId
from pymongo import ASCENDING
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.logger_helper import LoggerHelper
from server.models.user_model import RegisterModel, UpdateUserModel
from server.utils.auth_utils import hash_password, verify_password, create_token
from server.helpers.mongo_helper import MongoHelper


__mongo_helper = MongoHelper(allowed_collections=["users"])


def __create_index():
    __mongo_helper.create_index(
        "users",
        [("username", ASCENDING), ("email", ASCENDING)],
        name="UQ_EMAIL_USERNAME_IDX",
        unique=True,
    )


__create_index()

query = QueryType()
mutation = MutationType()


def user_to_dict(user):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "isAdmin": user.get("isAdmin", False),
    }


@query.field("users")
def resolve_users(_, info):
    users = __mongo_helper.find_many("users", {})
    return [user_to_dict(user) for user in users]


@query.field("user")
def resolve_user(_, info, id):
    user = __mongo_helper.find_one("users", {"_id": ObjectId(id)})
    if not user:
        return None
    return user_to_dict(user)


@mutation.field("register")
def resolve_register(_, info, input):
    model = RegisterModel(**input)
    hashed_pw = hash_password(model.password)
    user_data = {
        "username": model.username,
        "email": model.email,
        "password": hashed_pw,
        "isAdmin": False,
    }
    inserted_id = __mongo_helper.insert_one("users", user_data)
    user_data["_id"] = inserted_id

    token = create_token({"id": str(user_data["_id"])})
    return {"token": token, "user": user_to_dict(user_data)}


@mutation.field("login")
def resolve_login(_, info, input):
    user = __mongo_helper.find_one("users", {"username": input["username"]})
    if not user:
        raise CustomGraphQLExceptionHelper("Credenciales inválidas")

    if not verify_password(input["password"], user["password"]):
        raise CustomGraphQLExceptionHelper("Credenciales inválidas")

    token = create_token({"id": str(user["_id"])})
    return {"token": token, "user": user_to_dict(user)}


@mutation.field("recoverPassword")
def resolve_recover_password(_, info, email):
    user = __mongo_helper.find_one("users", {"email": email})
    if not user:
        return False
    # Aquí enviar email o token de recuperación (mock)
    return True


@mutation.field("updateUser")
def resolve_update_user(_, info, input):
    user_id = ObjectId(input["id"])

    # Separar id y validar sólo los campos editables
    model = UpdateUserModel(**input)

    # Crear diccionario solo con los campos no nulos que vienen en el input
    update_data = model.model_dump(exclude_unset=True)

    user = __mongo_helper.find_one("users", {"_id": user_id})
    if not user:
        raise CustomGraphQLExceptionHelper("Usuario no encontrado")
    if update_data:
        __mongo_helper.update_one("users", {"_id": user_id}, {"$set": update_data})

    user = __mongo_helper.find_one("users", {"_id": user_id})
    return user_to_dict(user)


@mutation.field("deleteUser")
def resolve_delete_user(_, info, id):
    result = __mongo_helper.delete_one("users", {"_id": ObjectId(id)})
    return result["deleted_count"] == 1


resolvers = [query, mutation]
