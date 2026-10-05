"""
Load configuration.

Order of precedence:
1. CLI arguments (highest)
2. config.yaml
3. Hard-coded defaults (lowest)

This is a common pattern. It lets you set defaults once
and override them for one run.
"""

import argparse
import yaml
from pathlib import Path


DEFAULTS = {
    "topics": ["agents"],
    "max_results_per_topic": 5,
    "digest_dir": "digest",
    "db_path": "data/memory.db",
}


def load_config(cli_args: argparse.Namespace | None = None) -> dict:
    """
    Load config from config.yaml, then override with CLI args.
    """
    config = dict(DEFAULTS)

    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        config.update(file_config)

    if cli_args is not None:
        if getattr(cli_args, "topics", None):
            config["topics"] = cli_args.topics
        if getattr(cli_args, "max_results", None):
            config["max_results_per_topic"] = cli_args.max_results

    return config


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="workflow-agent")
    parser.add_argument(
        "--topics",
        type=str,
        help="Comma-separated topics. Overrides config.yaml.",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        help="Max results per topic. Overrides config.yaml.",
    )
    args = parser.parse_args()
    if args.topics:
        args.topics = [t.strip() for t in args.topics.split(",")]
    return args
