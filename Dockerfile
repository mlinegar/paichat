# syntax=docker/dockerfile:1
FROM docker
COPY --from=docker/buildx-bin /buildx /opt/homebrew/bin/docker-buildx
RUN docker buildx version

FROM python:3.11

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
ADD . /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8089 available to the world outside this container
EXPOSE 8089

# Define environment variable
ENV NAME Chatbot

CMD ["lmql chat", "chat.lmql "]
