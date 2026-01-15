# Use the official uv image which comes with python and uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies using uv
# --frozen ensures we use the exact versions in uv.lock
RUN uv sync --frozen --no-dev

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
# uv run automatically uses the virtual environment created by uv sync
CMD ["uv", "run", "python", "-m", "app.app"]
