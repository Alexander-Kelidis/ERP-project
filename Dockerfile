# Step 1: Use an official Python runtime as a parent image
FROM python:3.11-slim

# Step 2: Install system dependencies needed to build some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    libffi-dev \
    libc-dev \
    libbz2-dev \
    zlib1g-dev \
    libssl-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libreadline-dev \
    libtk8.6 \
    tk-dev \
    libgdbm-dev \
    libdb5.3-dev \
    liblzma-dev \
    libgdbm-compat-dev \
    libsqlite3-dev \
    && apt-get clean

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the requirements file into the container at /app
COPY requirements.txt /app/

RUN pip install --upgrade pip

# Step 4: Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the current directory contents into the container at /app
COPY . /app/

# Step 6: Expose the port that the Django app will run on
EXPOSE 8000

# Step 7: Define environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Step 8: Run database migrations and start the Django development server
CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]