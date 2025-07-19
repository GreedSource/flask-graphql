from datetime import datetime, timezone
import os
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from server.constants.error_messages import (
    DEFAULT_DUPLICATE_MESSAGE,
    DUPLICATE_ERROR_MESSAGES,
)
from server.decorators.singleton_decorator import singleton
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.logger_helper import LoggerHelper


@singleton
class MongoHelper:
    def __init__(self, uri=None, allowed_collections=None):
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = MongoClient(self.uri)
        self.db = self.client[os.getenv("MONGO_DB_NAME", "graphqlapp")]
        self.allowed_collections = (
            set(allowed_collections) if allowed_collections else None
        )

    def _check_collection_allowed(self, name: str):
        if (
            self.allowed_collections is not None
            and name not in self.allowed_collections
        ):
            raise CustomGraphQLExceptionHelper(
                f"Acceso a colección '{name}' no permitido"
            )

    def get_collection(self, name):
        self._check_collection_allowed(name)
        return self.db[name]

    def create_index(
        self, collection_name: str, keys: list[tuple], name: str | None = None, **kwargs
    ):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        LoggerHelper.info(
            f"Creating index on: {collection_name} with keys {keys} and name {name}"
        )
        if name:
            kwargs["name"] = name

        return collection.create_index(keys, **kwargs)

    def create_ttl_index(self, collection_name: str, field_name, expire_seconds):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        index_name = collection.create_index(
            [(field_name, 1)], expireAfterSeconds=expire_seconds
        )
        return index_name

    def insert_one(self, collection_name: str, document: dict):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        try:
            now = datetime.now(timezone.utc)
            document["created_at"] = now
            document["updated_at"] = now
            result = collection.insert_one(document)
            return result.inserted_id
        except DuplicateKeyError as e:
            LoggerHelper.error(f"Documento duplicado: {str(e)}")
            message = DUPLICATE_ERROR_MESSAGES.get(
                collection_name, DEFAULT_DUPLICATE_MESSAGE
            )
            raise CustomGraphQLExceptionHelper(
                message,
                code="RESOURCE_ALREADY_EXISTS",
                details={"collection": collection_name},
            )
            raise CustomGraphQLExceptionHelper("Documento duplicado")
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper("Error al insertar documento: " + str(e))

    def find_one(self, collection_name: str, filter_, projection=None):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        return collection.find_one(filter_, projection)

    def find_many(
        self, collection_name: str, filter_, projection=None, skip=0, limit=0, sort=None
    ):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        cursor = collection.find(filter_, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update_one(
        self, collection_name: str, filter_: dict, update: dict, upsert=False
    ):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        if "$set" not in update:
            update["$set"] = {}

        update["$set"]["updated_at"] = datetime.now(timezone.utc)
        result = collection.update_one(filter_, update, upsert=upsert)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id,
        }

    def delete_one(self, collection_name: str, filter_: dict):
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]
        result = collection.delete_one(filter_)
        return {"deleted_count": result.deleted_count}

    def close(self):
        self.client.close()
