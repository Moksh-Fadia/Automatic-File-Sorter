# using a lightweight python base image
FROM python:3.11-slim

# set working directory inside container
WORKDIR /app

# copies all project files to container
COPY . /app

# installing dependencies
RUN pip install --no-cache-dir -r requirements.txt

# exposing fastapi port
EXPOSE 8000

# make FileSorter writable
RUN chmod -R 777 FileSorter

# command to start fastapi app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
