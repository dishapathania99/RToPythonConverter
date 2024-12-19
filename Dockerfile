# Use the rocker/verse image
FROM rocker/verse:latest

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt /app/requirements.txt

# Create a virtual environment and install Python dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

# Copy R library dependencies
COPY libraries.R /app/libraries.R

# Install R packages from libraries.R
RUN Rscript -e 'packages <- readLines("/app/libraries.R"); install.packages(packages, repos = "http://cran.us.r-project.org")'

# Copy the rest of the application code
COPY . /app

# Expose the application port
EXPOSE 5000

# Command to run the app
CMD ["/app/venv/bin/python", "app.py"]
