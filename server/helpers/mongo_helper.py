from datetime import datetime, timezone
import os
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import (
    DuplicateKeyError,
    PyMongoError,
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, UpdateResult, DeleteResult

from server.constants.error_messages import (
    DEFAULT_DUPLICATE_MESSAGE,
    DUPLICATE_ERROR_MESSAGES,
)
from server.decorators.singleton_decorator import singleton
from server.enums.http_error_code_enum import HTTPErrorCode
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.logger_helper import LoggerHelper


@singleton
class MongoHelper:
    """Clase mejorada para manejo de MongoDB con conexión robusta y manejo avanzado de errores"""

    def __init__(
        self,
        uri: Optional[str] = None,
        allowed_collections: Optional[List[str]] = None,
        connect_timeout_ms: int = 5000,
        socket_timeout_ms: int = 30000,
        max_pool_size: int = 100,
        retry_writes: bool = True,
    ):
        """
        Inicializa una conexión a MongoDB con validación y manejo robusto de errores

        Args:
            uri: URI de conexión (opcional, usa MONGO_URI por defecto)
            allowed_collections: Lista de colecciones permitidas
            connect_timeout_ms: Tiempo de espera para conexión (ms)
            socket_timeout_ms: Tiempo de espera para operaciones (ms)
            max_pool_size: Tamaño máximo del pool de conexiones
            retry_writes: Habilitar reintentos para operaciones de escritura
        """
        self.dbname = os.getenv("MONGO_DB_NAME", "graphqlapp")
        self.uri = uri or os.getenv("MONGO_URI")

        if not self.uri:
            raise ValueError(
                "MONGO_URI debe estar definido (como parámetro o variable de entorno)"
            )

        self.allowed_collections = (
            set(allowed_collections) if allowed_collections else None
        )
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None

        self._connect(
            connect_timeout_ms=connect_timeout_ms,
            socket_timeout_ms=socket_timeout_ms,
            max_pool_size=max_pool_size,
            retry_writes=retry_writes,
        )
        self._validate_connection()

    def _connect(
        self,
        connect_timeout_ms: int,
        socket_timeout_ms: int,
        max_pool_size: int,
        retry_writes: bool,
    ) -> None:
        """Establece la conexión con configuración robusta"""
        try:
            self.client = MongoClient(
                self.uri,
                connectTimeoutMS=connect_timeout_ms,
                socketTimeoutMS=socket_timeout_ms,
                serverSelectionTimeoutMS=connect_timeout_ms,
                maxPoolSize=max_pool_size,
                retryWrites=retry_writes,
                appname=self.dbname,
            )
            self.db = self.client[self.dbname]
        except ConnectionFailure as e:
            raise ConnectionError(f"Error de conexión a MongoDB: {str(e)}") from e
        except PyMongoError as e:
            raise RuntimeError(f"Error inicializando MongoDB: {str(e)}") from e

    def _validate_connection(self) -> None:
        """Valida que la conexión esté activa y funcional"""
        try:
            # Comando ligero para verificar conexión
            self.client.admin.command("ping")
            LoggerHelper.success(f"Conexión exitosa a MongoDB - DB: {self.dbname}")
        except ServerSelectionTimeoutError:
            raise ConnectionError("No se pudo conectar al servidor MongoDB (timeout)")
        except OperationFailure as e:
            raise ConnectionError(f"Error de autenticación/operación: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error validando conexión: {str(e)}")

    def _check_collection_allowed(self, collection_name: str) -> None:
        """Valida que la colección esté en la lista de permitidas"""
        if self.allowed_collections and collection_name not in self.allowed_collections:
            raise CustomGraphQLExceptionHelper(
                f"Acceso a colección '{collection_name}' no permitido. ",
                HTTPErrorCode.BAD_REQUEST,
            )

    def get_collection(self, name: str) -> Collection:
        """Obtiene una colección con validación previa"""
        self._check_collection_allowed(name)
        return self.db[name]

    def create_index(
        self,
        collection_name: str,
        keys: List[tuple],
        name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Crea un índice en la colección especificada

        Args:
            collection_name: Nombre de la colección
            keys: Lista de tuplas (campo, dirección)
            name: Nombre opcional del índice
            **kwargs: Argumentos adicionales para create_index

        Returns:
            Nombre del índice creado
        """
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]

        try:
            if name:
                kwargs["name"] = name

            index_name = collection.create_index(keys, **kwargs)
            LoggerHelper.info(f"Índice creado: {index_name} en {collection_name}")
            return index_name
        except OperationFailure as e:
            LoggerHelper.error(
                f"No se pudo crear índice: {index_name} en {collection_name}"
            )

    def create_ttl_index(
        self, collection_name: str, field_name: str, expire_seconds: int
    ) -> str:
        """
        Crea un índice TTL para expiración automática de documentos

        Args:
            collection_name: Nombre de la colección
            field_name: Campo que contiene la fecha de expiración
            expire_seconds: Segundos hasta la expiración

        Returns:
            Nombre del índice creado
        """
        return self.create_index(
            collection_name=collection_name,
            keys=[(field_name, 1)],
            expireAfterSeconds=expire_seconds,
            name=f"{field_name}_ttl_idx",
        )

    def insert_one(
        self, collection_name: str, document: Dict[str, Any], **kwargs
    ) -> InsertOneResult:
        """
        Inserta un documento con manejo de errores y timestamps automáticos

        Args:
            collection_name: Nombre de la colección
            document: Documento a insertar
            **kwargs: Argumentos adicionales para insert_one

        Returns:
            Resultado de la inserción
        """
        self._check_collection_allowed(collection_name)
        collection = self.db[collection_name]

        try:
            now = datetime.now(timezone.utc)
            document["created_at"] = now
            document["updated_at"] = now

            result = collection.insert_one(document, **kwargs)
            return result.inserted_id
        except DuplicateKeyError as e:
            LoggerHelper.error(f"Documento duplicado: {str(e)}")
            message = DUPLICATE_ERROR_MESSAGES.get(
                collection_name, DEFAULT_DUPLICATE_MESSAGE
            )
            raise CustomGraphQLExceptionHelper(
                message,
                code=HTTPErrorCode.CONFLICT,
                details={"collection": collection_name},
            )
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper(
                "Error al insertar documento: " + str(e), HTTPErrorCode.BAD_REQUEST
            )

    def find_one(
        self,
        collection_name: str,
        filter_: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Busca un documento con validación de colección"""
        self._check_collection_allowed(collection_name)
        try:
            return self.db[collection_name].find_one(filter_, projection, **kwargs)
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper(
                f"Error al buscar el documento: {str(e)}", HTTPErrorCode.BAD_REQUEST
            )

    def find_many(
        self,
        collection_name: str,
        filter_: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 0,
        sort: Optional[List[tuple]] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Busca múltiples documentos con opciones de paginación"""
        self._check_collection_allowed(collection_name)
        try:
            cursor = self.db[collection_name].find(filter_, projection, **kwargs)
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper(
                f"Error al buscar los documentos: {str(e)}", HTTPErrorCode.BAD_REQUEST
            )

    def update_one(
        self,
        collection_name: str,
        filter_: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        **kwargs,
    ) -> UpdateResult:
        """Actualiza un documento con timestamp automático"""
        self._check_collection_allowed(collection_name)
        try:
            if "$set" not in update:
                update["$set"] = {}

            update["$set"]["updated_at"] = datetime.now(timezone.utc)
            return self.db[collection_name].update_one(
                filter_, update, upsert=upsert, **kwargs
            )
        except DuplicateKeyError as e:
            LoggerHelper.error(f"Documento duplicado: {str(e)}")
            message = DUPLICATE_ERROR_MESSAGES.get(
                collection_name, DEFAULT_DUPLICATE_MESSAGE
            )
            raise CustomGraphQLExceptionHelper(
                message,
                code=HTTPErrorCode.CONFLICT,
                details={"collection": collection_name},
            )
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper(
                f"Error al actualizar el documento: {str(e)}", HTTPErrorCode.BAD_REQUEST
            )

    def delete_one(
        self, collection_name: str, filter_: Dict[str, Any], **kwargs
    ) -> DeleteResult:
        """Elimina un documento con validación"""
        self._check_collection_allowed(collection_name)
        try:
            return self.db[collection_name].delete_one(filter_, **kwargs)
        except PyMongoError as e:
            raise CustomGraphQLExceptionHelper(
                f"Error al eliminar el documento: {str(e)}", HTTPErrorCode.BAD_REQUEST
            )

    def close(self) -> None:
        """Cierra la conexión de manera segura"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def __enter__(self):
        """Para uso como context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garantiza el cierre de la conexión"""
        self.close()
