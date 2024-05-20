FROM python:3-alpine
LABEL authors="goan_vi"

WORKDIR /usr/src/app/
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY src ./src
ENTRYPOINT [ "python", "src/main.py" ]
