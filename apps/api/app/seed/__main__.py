import asyncio
import sys

from app.seed.runner import run_seed


def main() -> None:
    force = "--force" in sys.argv[1:]
    asyncio.run(run_seed(force=force))


if __name__ == "__main__":
    main()
