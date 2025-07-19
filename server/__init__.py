from flask import Flask, request, jsonify
from ariadne import graphql_sync
from ariadne.explorer import ExplorerGraphiQL

from schema import schema  # tu schema creado con Ariadne


def create_app():
    app = Flask(__name__)

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
            schema, data, context_value=request, debug=app.debug
        )
        status_code = 200 if success else 400
        return jsonify(result), status_code

    return app
