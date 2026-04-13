# Use Python 3.10 image
FROM python:3.10

# Set working directory inside container
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
# --use-deprecated=legacy-resolver helps with some future pip versions
RUN pip install --no-cache-dir -r requirements.txt

# Expose Django default port
EXPOSE 8000

# Proper CMD syntax (no space issues)
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
