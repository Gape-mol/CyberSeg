import os
from collections import defaultdict

from code_extractor import Languages, make_session, mine_repo, search_repos
from dotenv import load_dotenv
from file_manager import load_checkpoint, save_checkpoint, write_words

load_dotenv()


def main():
    token = os.getenv("GITHUB_TOKEN")

    words_path = "shared/words.json"
    checkpoint_path = "shared/checkpoint.json"
    per_page = 10

    session = make_session(token)
    checkpoint = load_checkpoint(checkpoint_path)
    page = checkpoint.get("page", 1)
    repo_start = checkpoint.get("repo_index", 0)

    total = defaultdict(lambda: defaultdict(int))
    total_repos = 0
    total_files = 0
    total_functions = 0

    while True:
        repos = search_repos(session, page=page, per_page=per_page)

        if not repos:
            page = 1
            repo_start = 0
            continue

        for i, repo in enumerate(repos):
            if i < repo_start:
                continue

            counts, files_in_repo, functions_in_repo = mine_repo(repo)

            merge_counts(total, counts)
            total_repos += 1
            total_files += files_in_repo
            total_functions += functions_in_repo

            write_words(
                path=words_path,
                words=counts_to_dict(total),
                stats={
                    "total_repos": total_repos,
                    "total_files": total_files,
                    "total_functions": total_functions,
                },
            )
            save_checkpoint(checkpoint_path, {"page": page, "repo_index": i + 1})

        page += 1
        repo_start = 0


def merge_counts(total, new_counts):
    for language in Languages:
        for word, count in new_counts.get(language, {}).items():
            total[language][word] += count
            total["all"][word] += count


def counts_to_dict(total):
    return {key: dict(val) for key, val in total.items()}


if __name__ == "__main__":
    main()
