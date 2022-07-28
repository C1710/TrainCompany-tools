FROM mcr.microsoft.com/vscode/devcontainers/python:3.9

COPY . /tools

VOLUME /TrainCompany-Data
ENV TRAINCOMPANY_DATA=/TrainCompany-Data
ENV TRAINCOMPANY_TOOLS_DATA=/tools/data

RUN python -m pip install -r tools/requirements.txt

ENTRYPOINT "/bin/bash"