# Fitness Solutions Server ⚡️

Fitness Solutions Server is developed and maintained by @Mads Odgaard and will be deployed on AWS with the help of CI/CD via GitHub Actions.

![Python](http://img.shields.io/badge/python-3.11.1-brightgreen.svg)
![FastAPI](http://img.shields.io/badge/fastapi-0.95.0-brightgreen.svg)
<a href="https://github.com/Fitness-Solutions/docs.git">
<img src="http://img.shields.io/badge/read_the-docs-2196f3.svg" alt="Documentation">
</a>

## Supported Platforms

Fitness Solutions Server will be supporting the following platforms:

- Ubuntu 22.04+

## Run Guide

Please make sure you create a `.env` file with the required environment variables.
Have a look at `.env.example` for at template. You also need to install [Poetry](https://python-poetry.org)

```
docker compose up # Start database server
poetry install
poetry shell
alembic upgrade head # Run migrations
uvicorn fitness_solutions_server.main:app --reload --host 0.0.0.0 # Start server
```

## Products

Fitness Solutions Server will host the API to support various Fitness Solutions products:

| Product                 | Platform       | Version |
| ----------------------- | -------------- | ------- |
| Gains                   | iOS            | v1.0.0  |
| Gains                   | Android        | v1.0.0  |
| Eat                     | iOS            | v1.0.0  |
| Eat                     | Android        | v1.0.0  |
| Fitness Coach App       | Cross platform | v1.0.0  |
| Fitness Solutions Admin | macOS Catalyst | v1.0.0  |
