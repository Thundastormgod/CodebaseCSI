# Production Dockerfile for AI Code Detector
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install package
RUN pip install --no-cache-dir -e .

# Create volume for code scanning
VOLUME ["/code"]

# Set default command
ENTRYPOINT ["ai-detector"]
CMD ["--help"]

# Labels
LABEL maintainer="AI Code Detector Team <contact@ai-code-detector.com>"
LABEL description="AI-generated code detection and analysis tool"
LABEL version="1.0.0"
