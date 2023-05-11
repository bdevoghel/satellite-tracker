ARG PYTHON_VERSION=3.10
FROM python:$PYTHON_VERSION AS base
WORKDIR /pointing

# Install Poetry.
ENV POETRY_VERSION=1.4.0
RUN pip install --no-cache-dir poetry~=$POETRY_VERSION

# Create and activate a virtual environment.
ENV VIRTUAL_ENV /opt/venv
RUN python -m venv ${VIRTUAL_ENV}
ENV PATH=${VIRTUAL_ENV}/bin:$PATH

# Install the dependencies
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --only main --no-root --no-interaction

# Copy and install the application code
COPY README.md .
COPY pointing pointing
RUN poetry install --only internal,main --no-interaction

FROM base as ci
RUN poetry install --with test
COPY tests tests
CMD [ "pytest" ]

FROM base as runtime
CMD [ "python", "pointing/main.py" ]
