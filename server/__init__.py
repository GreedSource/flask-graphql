import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL

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

    @app.route("/graphql", methods=["POST"])
    def graphql_server():
        data = request.get_json()
        success, result = graphql_sync(
            schema,
            data,
            context_value=request,
            debug=app.debug,
            error_formatter=custom_format_error,
        )
        status_code = 200 if success else 400
        return jsonify(result), status_code

    return app
