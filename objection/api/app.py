from flask import Flask

from . import rpc
from . import script
from . import agent_endpoints


def create_app() -> Flask:
    """
        Creates a new Flask instance for the objection API

        :return:
    """

    app = Flask(__name__)
    app.register_blueprint(rpc.bp)
    app.register_blueprint(script.bp)
    app.register_blueprint(agent_endpoints.bp)

    return app
