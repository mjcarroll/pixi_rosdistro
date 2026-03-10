FROM ubuntu:22.04

# Avoid interactive prompts during installations
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal system dependencies required by Pixi and some vendor packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Pixi (using the official install script)
RUN curl -fsSL https://pixi.sh/install.sh | bash
ENV PATH="/root/.pixi/bin:$PATH"

# Set up workspace
WORKDIR /workspace

# Ensure Pixi can use the mounted project immediately
# (The user will mount the current directory to /workspace)

# Default to a login shell so pixi activation works if configured
CMD ["/bin/bash"]
