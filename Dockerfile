# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY app/ ./app/

# Copy any necessary scripts or configuration files
COPY interview-content/ ./interview-content/

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]