# HexStrike AI — Docker Build Notes

## Known Issue: docker compose build hangs at "exporting layers"

`docker compose build hexstrike-ai` hangs at the buildkit "exporting layers" step when building the ~5.72GB image. This is a buildkit issue with large images.

### Working Build Command

```bash
docker build -t fake_ai_arxon-hexstrike-ai:latest external/hexstrike-ai/
```

### Why docker compose build fails

1. The hexstrike-ai image is large (~5.72GB) due to 50+ security tools
2. Buildkit's layer exporter appears to stall on large layers
3. Using `DOCKER_BUILDKIT=0` (legacy builder) also hangs because the build context is large

### Mitigations

- `.dockerignore` excludes `.git/`, `.omc/`, `__pycache__/`, `*.bak`, `*.log` to reduce build context
- Direct `docker build` avoids the compose buildkit layer export path
- Build typically completes in ~22 seconds with direct `docker build`

### Rebuild after code changes

```bash
# Rebuild the image
docker build -t fake_ai_arxon-hexstrike-ai:latest external/hexstrike-ai/

# Restart the container
docker compose up -d hexstrike-ai
```
