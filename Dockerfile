# Use a base image with Conda installed
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app

# Copy a simple Python script into the container
COPY test_server.py /app/test_server.py

# Make port 18089 available to the world outside this container
EXPOSE 18089

# Command to run the test server
CMD ["python", "test_server.py"]
