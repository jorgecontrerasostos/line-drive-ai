# line-drive-ai

A Python project created with uv and ruff.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and [ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the application:
   ```bash
   uv run line-drive-ai
   ```

### Development Commands

- Run tests:
  ```bash
  uv run pytest
  ```

- Run tests with coverage:
  ```bash
  uv run pytest --cov
  ```

- Lint code:
  ```bash
  uv run ruff check
  ```

- Format code:
  ```bash
  uv run ruff format
  ```

- Check and fix linting issues:
  ```bash
  uv run ruff check --fix
  ```
