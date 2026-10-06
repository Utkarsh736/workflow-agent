"""
Direct tool test. No agent loop.

Use this to test tools in isolation.
For the real agent, use run_agent.py.
"""

from dotenv import load_dotenv
load_dotenv()

from agent.config import load_config, parse_args
from agent.tools import search_arxiv, summarize_paper
from agent.memory import check_seen, mark_seen, count_seen


def main():
    args = parse_args()
    config = load_config(args)

    print(f"Topics: {config['topics']}")
    print(f"Max per topic: {config['max_results_per_topic']}")
    print(f"Model: {config['llm_model']}")
    print("-" * 60)

    new_papers = []
    total_tokens = 0

    for topic in config["topics"]:
        print(f"\n[search] topic: {topic}")
        papers = search_arxiv(
            topic,
            max_results=config["max_results_per_topic"],
        )

        for paper in papers:
            if check_seen(paper["id"], db_path=config["db_path"]):
                print(f"  [skip] already seen: {paper['id']}")
                continue

            print(f"  [new]  {paper['title']}")
            print(f"         summarizing...")

            try:
                result = summarize_paper(
                    title=paper["title"],
                    abstract=paper["abstract"],
                    model=config["llm_model"],
                    max_tokens=config["llm_max_tokens"],
                    temperature=config["llm_temperature"],
                )
            except Exception as e:
                print(f"         [error] summary failed: {e}")
                continue

            paper["summary"] = result["summary"]
            paper["tokens"] = result["total_tokens"]
            total_tokens += result["total_tokens"]

            mark_seen(
                paper["id"],
                paper["title"],
                db_path=config["db_path"],
            )
            new_papers.append(paper)


    print("-" * 60)
    print(f"New papers summarized: {len(new_papers)}")
    print(f"Total tokens used: {total_tokens}")
    print(f"Total in memory: {count_seen(config['db_path'])}")


if __name__ == "__main__":
    main()