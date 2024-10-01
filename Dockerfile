FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV MAX_DEPTH=2
ENV SCRIPT_NAME=non_citizen_voting_v6
ENV INTERNAL_PORT=8089
ENV HOST=0.0.0.0

CMD ["python", "launch_chatserver2.py"]