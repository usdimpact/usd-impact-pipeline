FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1

COPY wheelhouse /wheelhouse
COPY requirements.lock /frozen/requirements.lock

RUN python -m pip install --disable-pip-version-check --no-index --only-binary=:all: --find-links=/wheelhouse -r /frozen/requirements.lock \
    && python -m pip check \
    && rm -rf /root/.cache/pip

COPY repo /app

RUN useradd --uid 65532 --no-create-home --shell /usr/sbin/nologin research \
    && mkdir -p /work /output \
    && chown -R 65532:65532 /work /output

USER 65532:65532
WORKDIR /app
ENTRYPOINT ["python", "-m", "scripts.run_frozen_research"]
