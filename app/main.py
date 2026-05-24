from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

# Initialize the FastAPI App with rich OpenAPI metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "An intelligent, end-to-end backend platform designed for the Steps AI National-Level Hackathon 2026. "
        "It automates resume parsing, interactive conversational mock interviews, and multi-dimensional "
        "performance grading with detailed suggestions and reports."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS (Cross-Origin Resource Sharing) Middlewares
# Enables frontend clients or browser tools to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to trusted domains in a production configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the master router containing API paths under "/api" prefix
app.include_router(api_router, prefix="/api")

@app.get("/", include_in_schema=False)
def root_redirect():
    """
    Root endpoint offering greetings and guiding developers to interactive Swagger UI.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API. Please navigate to /docs to explore the interactive API schema.",
        "docs": "/docs"
    }
