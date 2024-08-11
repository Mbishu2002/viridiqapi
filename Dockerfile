# Use the official Python image from Docker Hub
FROM python:3.11

# Set environment variables that are needed during the build
# These are declared as ARG and will not persist in the final image
ARG EMAIL_HOST_USER
ARG EMAIL_HOST_PASSWORD
ARG EMAIL_FROM
ARG FRONTEND_URL
ARG ENCRYPTION_KEY
ARG SUPERUSER_PASSWORD

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
ENV EMAIL_HOST=smtp.gmail.com
ENV EMAIL_PORT=587
ENV EMAIL_USE_TLS=True
ENV EMAIL_HOST_USER=${EMAIL_HOST_USER}
ENV EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
ENV EMAIL_FROM=${EMAIL_FROM}
ENV FRONTEND_URL=${FRONTEND_URL}
ENV ENCRYPTION_KEY=${ENCRYPTION_KEY}
ENV DJANGO_SUPERUSER_EMAIL=admin@viridiq.com
ENV DJANGO_SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD}

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port on which the app will run
EXPOSE 8000


# Run collectstatic, makemigrations, migrate, create superuser, and start the server
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py makemigrations && python manage.py migrate && python manage.py create_superuser && python manage.py runserver 0.0.0.0:8000"]
