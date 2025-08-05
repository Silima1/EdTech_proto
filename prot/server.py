import os
import sys
from pathlib import Path
from typing import Mapping

import sanic
from orjson import dumps
from sanic import Sanic, json
from sanic.worker.loader import AppLoader
from sanic_ext import Extend, validate
from dotenv import load_dotenv

from validators import GradeAssignmentPostModel
from db import create_new_task, fetch_finished_tasks

# Carrega variáveis do .env
load_dotenv()

PROD = os.environ.get("PRODUCTION") == "True"
SERVER_CONFIG: Mapping = {
    "host": os.getenv("HTTP_HOST", "0.0.0.0"),
    "port": int(os.getenv("HTTP_PORT", 50051)),
    "access_log": False,
    "workers": int(os.getenv("HTTP_WORKERS", 1)),
    "fast": False,
}

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            "format": "%(asctime)s - [%(process)d](%(name)s)[%(levelname)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "standardStream": {
            "class": "logging.StreamHandler",
            "formatter": "base",
            "stream": sys.stdout,
        }
    },
    "loggers": {"nexgencore": {"level": "INFO", "handlers": ["standardStream"]}},
}


def create_app(srv_name: str):
    app = Sanic(srv_name, dumps=dumps, log_config=LOGGING_CONFIG)
    Extend(app)

    app.config.FALLBACK_ERROR_FORMAT = "json"
    app.config.OAS_CUSTOM_FILE = (
        Path(__file__).resolve().parents[1] / "openapi.yaml"
    )
    app.config.oas_ui_swagger = False
    app.config.oas_autodoc = False

    if PROD:
        app.config.oas_ui_redoc = False

    @app.post("/grade-assignment")
    @validate(json=GradeAssignmentPostModel)
    async def grade_assignment(request: sanic.Request, body: GradeAssignmentPostModel):
        task_id: int = create_new_task(body.user_id, body.submission_id, body.assignment_id)
        return json({"task_id": task_id}, status=202)

    @app.get("/results")
    async def get_results(request: sanic.Request):
        finished_tasks = fetch_finished_tasks()
        return json({"results": finished_tasks}, status=200)

    return app


loader = AppLoader(factory=lambda: create_app(__name__))
app = loader.load()
app.prepare(**SERVER_CONFIG)
Sanic.serve(primary=app, app_loader=loader)