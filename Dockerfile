FROM python:3.7.2

# setup of client
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# run client
ENTRYPOINT ["python", "thorcast_slack.py"]