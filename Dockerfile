FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# The project does not yet include a dependency manifest. Pin Django to the
# version used by the project so the image remains reproducible.
RUN pip install --no-cache-dir "Django==6.1"

COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
