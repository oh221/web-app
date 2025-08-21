# Use the official Jenkins LTS image as base
FROM jenkins/jenkins:lts

# Switch to root to install system packages
USER root

# Update package lists and install Python, Docker CLI, and other dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    wget \
    git \
    build-essential \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for easier access
RUN ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# Install Docker CLI (for Docker commands inside Jenkins)
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# Install Docker Compose (standalone binary)
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Create a Python virtual environment for Jenkins jobs
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install useful Python packages for CI/CD
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    virtualenv \
    pytest \
    flake8 \
    black \
    isort \
    safety \
    bandit \
    coverage \
    django

# Create workspace directory with proper permissions
RUN mkdir -p /workspace && chown -R jenkins:jenkins /workspace

# Make virtual environment accessible to jenkins user
RUN chown -R jenkins:jenkins /opt/venv

# Switch back to Jenkins user
USER jenkins

# Install some Jenkins plugins (optional)
RUN jenkins-plugin-cli --plugins \
    git \
    workflow-aggregator \
    docker-workflow \
    pipeline-stage-view \
    blueocean \
    timestamper \
    build-timeout \
    credentials-binding \
    ws-cleanup

# Set Python env vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHON_VERSION=3.11

# Health check to ensure Jenkins is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/login || exit 1

# Expose Jenkins ports
EXPOSE 8080 50000
