FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system-level packages
RUN apt-get update && \
    apt-get install -y git default-jre graphviz   && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements early to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy rest of the app code
COPY ./app /app

# Expose the Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
