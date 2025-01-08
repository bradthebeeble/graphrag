"""CLI implementation of the load subcommand."""

import logging
import warnings
import sys
import asyncio

from pathlib import Path

import graphrag.api as api

from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.config.load_config import load_config
from graphrag.config.resolve_path import resolve_paths
from graphrag.config.logging import enable_logging_with_config
from graphrag.utils.cli import redact

from graphrag.logger.base import ProgressLogger

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*NumbaDeprecationWarning.*")

log = logging.getLogger(__name__)


def _logger(logger: ProgressLogger):
    def info(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.info(msg)

    def error(msg: str, verbose: bool = False):
        log.error(msg)
        if verbose:
            logger.error(msg)

    def success(msg: str, verbose: bool = False):
        log.info(msg)
        if verbose:
            logger.success(msg)

    return info, error, success

def _register_signal_handlers(logger: ProgressLogger):
    import signal

    def handle_signal(signum, _):
        # Handle the signal here
        logger.info(f"Received signal {signum}, exiting...")  # noqa: G004
        logger.dispose()
        for task in asyncio.all_tasks():
            task.cancel()
        logger.info("All tasks cancelled. Exiting...")

    # Register signal handlers for SIGINT and SIGHUP
    signal.signal(signal.SIGINT, handle_signal)

    if sys.platform != "win32":
        signal.signal(signal.SIGHUP, handle_signal)

def load_cli(
    root_dir: Path,
    verbose: bool,
    logger: LoggerType,
    config_filepath: Path | None,
    output_dir: Path | None,
    load_communities: bool = False
):
    """Run the pipeline with the given config."""
    config = load_config(root_dir, config_filepath)

    _run_load(
        config=config,
        verbose=verbose,
        logger=logger,
        output_dir=output_dir,
        load_communities=load_communities
    )

def _run_load(
    config,
    verbose,
    logger,
    output_dir,
    load_communities
):
    progress_logger = LoggerFactory().create_logger(logger)
    info, error, success = _logger(progress_logger)
    config.storage.base_dir = str(output_dir) if output_dir else config.storage.base_dir
    config.reporting.base_dir = (
        str(output_dir) if output_dir else config.reporting.base_dir
    )
    resolve_paths(config)

    enabled_logging, log_path = enable_logging_with_config(config, verbose)
    if enabled_logging:
        info(f"Logging enabled at {log_path}", True)
    else:
        info(
            f"Logging not enabled for config {redact(config.model_dump())}",
            True,
        )
    _register_signal_handlers(progress_logger)

    output = api.load_data(
            config=config,
            progress_logger=progress_logger,
            load_communities=load_communities
    )
    encountered_errors = not output

    progress_logger.stop()
    if encountered_errors:
        error(
            "Errors occurred during the pipeline run, see logs for more details.", True
        )
    else:
        success("Loading to graph db completed successfully.", True)

    sys.exit(1 if encountered_errors else 0)
