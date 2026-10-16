# rlp-template-python-fastapi

The first certified [rlp](https://github.com/rdlucas2/rlp) template: a hello-world FastAPI service that renders a valid `rlp.yaml` and passes every golden-pipeline gate out of the box. It is the reference implementation of the rlp contract; later templates copy its structure.

## Use it

```sh
rlp new gh:rdlucas2/rlp-template-python-fastapi my-service
cd my-service
rlp setup && rlp test
rlp run          # in one terminal
rlp smoke        # in another
```

Questions (see `copier.yml`):

| Question | Default | Meaning |
| --- | --- | --- |
| `project_id` | `hello-api` | `metadata.name` and `metadata.project`; also the Python distribution name (`-` becomes `_` for the package) |
| `component_name` | `api` | The component's name in `rlp.yaml` |
| `python_version` | `3.13` | `3.13` or `3.12`: the image base and `.python-version` |
| `port` | `8000` | Port the service listens on |
| `coverage_minimum` | `80` | `quality.coverage.minimum`; 70 (the platform floor) to 100 |

## What a rendered repo contains

| File | Purpose |
| --- | --- |
| `rlp.yaml` | The contract: one `container-service` component with `/healthz` and `/readyz`, a sample Postgres service, config and telemetry |
| `Taskfile.yml` | The seven standard verbs, implemented with `uv` |
| `pyproject.toml`, `uv.lock` | Pinned dependencies; `uv sync --locked` installs exactly the lock |
| `src/<package>/` | The FastAPI app: config only from environment variables, JSON logs to stdout, OpenTelemetry tracing driven by the standard `OTEL_*` variables, and a smoke checker |
| `tests/` | pytest with JUnit XML and Cobertura coverage written to the paths `rlp.yaml` declares |
| `Dockerfile` | Multi-stage build on a pinned `python:<version>-slim` base, running as a non-root user |
| `.pre-commit-config.yaml`, `.yamllint.yaml`, `.editorconfig` | The rlp conventions |
| `.github/workflows/pipeline.yml` | Calls the rlp golden pipeline, pinned to an rlp commit |
| `.copier-answers.yml` | Lets `rlp update` move the repo to a newer template version |

## This repo

- `copier.yml`: the questions; the template files live in `template/`.
- `rlp-template.yaml`: the template contract, checked by `rlp validate` and `rlp policy check`.
- `tests/default-answers.yml`: the answers the conformance loop renders with.

`uv.lock` is rendered from `template/uv.lock.jinja`; only the project name is templated. To change dependencies, render the template, edit `pyproject.toml`, run `uv lock`, and copy the result back, replacing the project name with `{{ project_id }}`.

In `template/Dockerfile.jinja`, template variables are written without spaces (`{{port}}`), so `rlp policy check` can still parse the file in this repo.
