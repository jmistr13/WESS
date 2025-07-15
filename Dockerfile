FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Remove Windows-only packages
RUN sed -i '/pywin32/d;/pywinpty/d' requirements.txt

# Let pip handle versioning or downgrade pyviz_comms if needed
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python"]
