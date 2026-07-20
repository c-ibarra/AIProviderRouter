"""Process entrypoint: fail-fast startup checks, logging setup, then serve
the FastAPI app bound to 127.0.0.1 only — never 0.0.0.0 (NFR-01, resolved
decision: no router-level auth, localhost binding is the only access control).
"""

import os

import uvicorn

from router.adapters.http.app import create_app
from router.adapters.http.logging_config import configure_logging
from router.adapters.http.startup import validate_startup

HOST = "127.0.0.1"
PORT = 8000
REQUIRED_CLIS = ["claude", "agy"]


def main() -> None:
    validate_startup(REQUIRED_CLIS)
    configure_logging(level=os.environ.get("AI_PROVIDER_ROUTER_LOG_LEVEL", "INFO"))
    app = create_app()
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
