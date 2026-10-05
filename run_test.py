"""
First runnable step.

This script calls search_arxiv and prints the results.
No LLM. No memory. No agent loop.
"""

import argparse
from agent.tools import search_arxiv


def main():
    parser = argparse.ArgumentParser(description="Test arXiv search.")
    parser.add_argument(
        "--topic",
        type=str,
        default="agents",
        help="Topic to search for. Default: agents",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=3,
        help="Max results. Default: 3",
    )
    args = parser.parse_args()

    print(f"Searching arXiv for: {args.topic}")
    print(f"Max results: {args.max}")
    print("-" * 60)

    papers = search_arxiv(args.topic, max_results=args.max)

    for i, p in enumerate(papers, 1):
        print(f"\n[{i}] {p['title']}")
        print(f"    ID: {p['id']}")
        print(f"    Published: {p['published']}")
        print(f"    URL: {p['url']}")
        print(f"    Abstract: {p['abstract'][:200]}...")


if __name__ == "__main__":
    main()
