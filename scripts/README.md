# Docker Scripts

Scripts to manage Docker services for the project.

## Available scripts

### `docker-up.sh`
Starts Docker services (PostgreSQL and Redis) in detached mode.

```bash
./scripts/docker-up.sh
```

### `docker-down.sh`
Stops Docker services while keeping volumes (data).

```bash
./scripts/docker-down.sh
```

### `docker-clean.sh`
Fully cleans Docker by removing containers, volumes, and networks.
**⚠️ WARNING: Removes all PostgreSQL and Redis data.**

```bash
./scripts/docker-clean.sh
```

### `docker-logs.sh`
Shows Docker service logs in real time.

```bash
# View logs for all services
./scripts/docker-logs.sh

# View logs for a specific service
./scripts/docker-logs.sh postgres
./scripts/docker-logs.sh redis
```

### `init.sh`
Initializes the full project: starts Docker, waits for PostgreSQL, and runs Alembic migrations.

```bash
./scripts/init.sh
```

### `restart.sh`
Fully restarts the project: cleans Docker, starts it again, and runs migrations.

```bash
./scripts/restart.sh
```

## Making scripts executable

If the scripts are not executable, run:

```bash
chmod +x scripts/*.sh
```

## Recommended workflow

### First time (or after cloning)
```bash
./scripts/init.sh
uvicorn app.main:app --reload
```

### Daily development
```bash
./scripts/docker-up.sh
uvicorn app.main:app --reload
```

### Clean everything and start fresh
```bash
./scripts/restart.sh
uvicorn app.main:app --reload
```

### When finished
```bash
./scripts/docker-down.sh
```
