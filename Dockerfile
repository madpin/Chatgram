# Use Python 3.9.16 image 
FROM python:3.9.16-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create app directory
WORKDIR /app

RUN apt-get update -y && apt-get install -y gcc

RUN pip install -U pip

# Install dependencies
COPY requirements.frozen .
RUN pip install -r requirements.frozen

# Copy source code
COPY chatgram/main.py . 
COPY chatgram/Chatbot.py .
COPY chatgram/TGPersonas.py .
COPY chatgram/model.py .
COPY chatgram/NiceGui.py .
COPY personas.yml .

# Build app
# RUN python setup.py install

# Expose port and start app 
# EXPOSE 80
CMD ["python", "main.py"]
