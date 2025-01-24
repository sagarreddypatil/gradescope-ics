FROM ghcr.io/astral-sh/uv:python3.12-alpine

ADD . /app

WORKDIR /app
RUN uv sync --frozen

EXPOSE 5000
CMD ["uv", "run", "gunicorn", "app:app", "--bind", "0.0.0.0:5000"]