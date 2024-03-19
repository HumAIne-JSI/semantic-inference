# Use the official Python image from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Clone the Git repository into the container
RUN apt-get update && apt-get install -y git
RUN apt-get install -y g++
RUN apt-get install -y libpq-dev python3-dev
RUN git clone --depth 1 https://github.com/openai/chatgpt-retrieval-plugin.git
COPY setup.sh .

COPY requirements.txt .
COPY runPlugin.sh .
COPY .env .
COPY *.py .
COPY Knowledge-Graph-Test-config.ttl .
RUN pip install -r requirements.txt
RUN pip install poetry
RUN pip uninstall -y urllib3
RUN pip install --upgrade urllib3

RUN ./setup.sh


# Expose the port the app runs on
EXPOSE 5000

RUN ./runPlugin.sh &
# Command to run the application

CMD ["python", "app.py"]
