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
| `code_owners` | `@rdlucas2` | Who reviews gate changes: GitHub users or teams, space-separated, written to `.github/CODEOWNERS` |

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
| `.github/workflows/pipeline.yml` | Calls the rlp golden pipeline, pinned to an rlp commit; runs on pull requests and on pull request reviews, so golden's `gate-review` re-checks when a review lands |
| `.github/CODEOWNERS` | Routes a change to a gate file (the paths the `rlp.agent` rules protect) to the `code_owners` for review |
| `.copier-answers.yml` | Lets `rlp update` move the repo to a newer template version |

## This repo

- `copier.yml`: the questions; the template files live in `template/`.
- `rlp-template.yaml`: the template contract, checked by `rlp validate` and `rlp policy check`.
- `tests/default-answers.yml`: the answers the conformance loop renders with.

- `.github/workflows/conformance.yml`: certifies the template on every PR, on `main`, on `v*` tags and weekly (see below).
- `.github/workflows/gate-review.yml`: rlp's `gate-review` check on every PR and PR review. An agent-authored PR (labelled `agent:authored`, or opened by an rlp agent account) that changes a gate file stays pending until a human who is neither its author nor an agent approves its head commit; any other PR passes. A gate file is one the `rlp.agent` rules flag or one `.github/CODEOWNERS` lists; `.github/scripts/gate_changes.py` collects them for `rlp pipeline gate-review`. It pins its own rlp commit, since `conformance.yml`'s is older than `gate-review`.
- `.github/CODEOWNERS`: this repo's gate files (workflows, lint settings, certification inputs, and the gates the template renders under `template/`), owned by `@rdlucas2`.

## Releases are certified

A release of this template is a GitHub Release, and only a certified commit gets one. `.github/workflows/conformance.yml` calls rlp's reusable [`template-conformance.yml`](https://github.com/rdlucas2/rlp/blob/main/docs/conformance.md), pinned to an rlp commit, which runs `rlp template certify`:

1. Validate `rlp-template.yaml` and render the template with `tests/default-answers.yml`.
2. Run the golden-pipeline gates on the rendered repo (pre-commit, policy, tests and coverage, SAST, secrets, package, Trivy); deploy is not part of certification.
3. Run `build`, then `rlp run`, `rlp smoke` and `rlp down` on the rendered repo.

The `conformance / certify` check runs on every PR and on `main`, and weekly so new CVEs in the rendered repo's dependencies or base image show up without a code change. A PR that breaks a verb, drops coverage below the minimum or adds a vulnerable dependency fails it. The conformance report is uploaded as the `rlp-conformance-report` artifact and summarised on the run page.

To release, bump `metadata.version` in `rlp-template.yaml`, merge, and push a matching tag from `main`:

```sh
git tag v0.1.0 && git push origin v0.1.0
```

On a `v*` tag, the `conformance / release` job runs only after certify passed, checks that the report says `certified`, and publishes the tag's GitHub Release with `conformance.json` attached. A tag that fails certification gets no release. To certify against a newer rlp, update both pinned SHAs in `conformance.yml` together.

`uv.lock` is rendered from `template/uv.lock.jinja`; only the project name is templated. To change dependencies, render the template, edit `pyproject.toml`, run `uv lock`, and copy the result back, replacing the project name with `{{ project_id }}`.

In `template/Dockerfile.jinja`, template variables are written without spaces (`{{port}}`), so `rlp policy check` can still parse the file in this repo.
