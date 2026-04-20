FROM python:3.12-slim

WORKDIR /app

# Install Dash dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source code
COPY . .

EXPOSE 8050
CMD ["python", "app.py"]
