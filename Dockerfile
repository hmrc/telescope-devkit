FROM python:3.9

ARG APP_PACKAGE_NAME=telescope_devkit

ENV TERM xterm-256color

COPY . /app/

WORKDIR /app

RUN pip install --upgrade pip poetry \
    && poetry config virtualenvs.create false \
    && poetry build -f wheel -v \
    && pip3 install dist/${APP_PACKAGE_NAME}-*.whl

RUN PYTHON_PKGS_DIR=$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])') \
    && rm -r ${PYTHON_PKGS_DIR}/telemetry/${APP_PACKAGE_NAME} \
    && ln -sfn /app/telemetry/${APP_PACKAGE_NAME} ${PYTHON_PKGS_DIR}/telemetry/

ENTRYPOINT ["python", "bin/telescope.py"]
