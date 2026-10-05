"""
First runnable step: search arXiv and use memory.

This script:
1. Loads config (file + CLI override).
2. Searches arXiv for each topic.
3. Filters out papers already seen.
4. Marks new papers as seen.
5. Prints results.
"""

from agent.config import load_config, parse_args
from agent.tools import search_arxiv
from agent.memory import check_seen, mark_seen, count_seen


def main():
    args = parse_args()
    config = load_config(args)

    print(f"Topics: {config['topics']}")
    print(f"Max per topic: {config['max_results_per_topic']}")
    print(f"DB: {config['db_path']}")
    print("-" * 60)

    new_papers = []

    for topic in config["topics"]:
        print(f"\n[search] topic: {topic}")
        papers = search_arxiv(topic, max_results=config["max_results_per_topic"])

        for paper in papers:
            if check_seen(paper["id"], db_path=config["db_path"]):
                print(f"  [skip] already seen: {paper['id']}")
                continue
            mark_seen(paper["id"], paper["title"], db_path=config["db_path"])
            new_papers.append(paper)
            print(f"  [new]  {paper['title']}")

    print("-" * 60)
    print(f"New papers: {len(new_papers)}")
    print(f"Total in memory: {count_seen(config['db_path'])}")


if __name__ == "__main__":
    main()