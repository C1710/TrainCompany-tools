FROM python:3.9

RUN apt-get -y update && apt-get install -y git dos2unix less sudo fonts-roboto && rm -rf /var/lib/apt/lists/*

COPY . /tools
RUN dos2unix /tools/*.py
RUN bash -c 'chmod a+rx /tools/{cleanup,convert_coordinates,create_tasks,export_station_list,import_{brouter,stations,trassenfinder},plot,project_coordinates,validate_files}.py'
RUN useradd -m traincompany
USER traincompany
# https://stackoverflow.com/a/38742545/5070653
# https://stackoverflow.com/questions/27093612/in-a-dockerfile-how-to-update-path-environment-variable#comment105601130_38742545
ENV PATH="/tools:$PATH"
RUN python -m pip install -r /tools/requirements.txt

VOLUME /TrainCompany-Data
ENV TRAINCOMPANY_DATA=/TrainCompany-Data
ENV TRAINCOMPANY_TOOLS_DATA=/tools/data


ENTRYPOINT "/bin/bash"