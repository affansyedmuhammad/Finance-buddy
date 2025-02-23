# Use an official Python runtime as a parent image
FROM python:3.11.9

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container at /app
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /code/app/

# Copy model file
COPY ./app/data/lstm_model.h5 /code/app/data/lstm_model.h5

# Copy environment variables file
COPY ./app/.env /code/.env

# Make port 80 available to the world outside this container
EXPOSE 80

# Run FastAPI server when the container launches
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]