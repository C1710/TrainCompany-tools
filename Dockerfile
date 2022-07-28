FROM python:3.9

COPY . /tools

RUN python -m pip install -r tools/requirements.txt
