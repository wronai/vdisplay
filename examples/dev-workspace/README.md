# Dev workspace

Development container with the repository mounted for live edits.

- Docs: [docs/examples.md](../../docs/examples.md)
- Main README: [README.md](../../README.md)

## Run interactive shell

```bash
cd examples/dev-workspace
docker compose run --rm dev
```

Inside the container:

```bash
pytest tests/ -v
vdisplay info
python -c "from vdisplay import VirtualDisplaySession; ..."
```

## Run a quick screenshot test

```bash
docker compose run --rm dev python examples/headless-virtual/run_virtual.py
```

The repo is mounted at `/app`, so code changes on the host are visible immediately.
