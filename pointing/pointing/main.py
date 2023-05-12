"""Program entrypoint for pointing module."""
import logging

logger = logging.getLogger(__name__)


def point():
    """Point to a satellite."""
    logger.info("Pointing ...")


if __name__ == "__main__":
    point()
