# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any needed for scipy/numpy, usually wheels cover it)
# and install uv
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure uv is in the PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy the project files into the container
COPY . .

# Install dependencies using uv
# --system flag installs into the system python, avoiding virtualenv overhead in docker
RUN uv sync --frozen

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
# We use 'python -m app.app' directly as uv sync installed packages to system python
# Or we can use 'uv run' but direct python is often cleaner in docker if installed globally
# However, 'uv sync' by default creates a .venv. 
# Let's use 'uv run' to be consistent with dev environment.
CMD ["uv", "run", "python", "-m", "app.app"]
