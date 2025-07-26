import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL

from server.enums.http_error_code_enum import HTTPErrorCode
from server.helpers.logger_helper import LoggerHelper
from server.helpers.mail_helper import MailHelper
from server.schema import schema
from server.utils.custom_error_formatter_utils import (
    custom_format_error,
)  # tu schema creado con Ariadne

# Desactiva completamente el logger que imprime el traceback
logging.getLogger("ariadne").setLevel(logging.CRITICAL)


def create_app():
    app = Flask(__name__)
    # Habilita CORS para todas las rutas y orígenes
    CORS(app, resources={r"/graphql": {"origins": "*"}})
    explorer_html = ExplorerGraphiQL().html(None)

    MailHelper().init_app(app)

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"status": "Ok", "message": "Welcome!!"})

    @app.route("/ping", methods=["GET"])
    def health_check():
        return jsonify({"status": "Ok", "message": "Pong"})

    @app.route("/graphql", methods=["GET"])
    def graphql_explorer():
        # Sirve GraphiQL UI para hacer queries
        return explorer_html, 200

    # Ejemplo función Flask con graphql_sync (suponiendo schema y custom_format_error definidos)

    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        data = request.get_json()
        operation_name = data.get("operationName", "unnamed")
        LoggerHelper.info(f"GraphQL operation: {operation_name}")

        success, result = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=app.debug,
            error_formatter=custom_format_error,
        )

        status_code = 200 if success else HTTPErrorCode.BAD_REQUEST.status_code

        # Ajustar status_code según código de error en extensions.code
        if "errors" in result:
            for err in result["errors"]:
                code = err.get("extensions", {}).get("code", "")
                # Mapea el código string a enum si existe
                for error_enum in HTTPErrorCode:
                    if code == error_enum.code_name:
                        status_code = error_enum.status_code
                        break
                # Si ya asignaste un código distinto de 200, no sigas buscando
                if status_code != HTTPErrorCode.BAD_REQUEST.status_code:
                    break

        return jsonify(result), status_code

    return app
