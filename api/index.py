import os
import sys

# Vercel serverless entrypoint: expose the FastAPI ASGI app.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentpay.server import app  # noqa: E402,F401  (Vercel detects ASGI `app`)
