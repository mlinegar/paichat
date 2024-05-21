# Use a base image with Conda installed
FROM continuumio/miniconda3

# Set the working directory in the container
WORKDIR /app


# Copy the Conda environment file
COPY environment.yml /app/environment.yml

# Create the Conda environment
RUN conda env create -f environment.yml

# Activate the environment
SHELL ["conda", "run", "-n", ".paichat", "/bin/bash", "-c"]

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 18089 available to the world outside this container
EXPOSE 18089

CMD ["python", "test_server.py"]

# Define environment variable
ENV NAME World

# Run lmql chat when the container launches
# CMD ["conda", "run", "-n", ".paichat", "lmql", "chat", "chat.lmql"]
CMD ["conda", "run", "-n", ".paichat", "python", "launch_chatserver.py"]