# Base image with CUDA support for PyTorch / Ray GPU acceleration
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during apt-get
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies and Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Install Poetry for dependency management
RUN pip3 install poetry==1.7.1

# Copy dependency files first to leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# Install dependencies without creating a virtualenv (we are already in an isolated container)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root --with dev

# Copy the rest of the enterprise codebase
COPY . .

# Default command to run training
CMD ["python3", "-m", "qts_core.models.trainer"]