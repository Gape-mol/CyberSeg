import os
import shutil
import subprocess
import time
from collections import defaultdict

import requests
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

Base_Url = "https://api.github.com"
Max_Attempts = 5
Temp_Folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")

Languages = ["python", "java"]

Extensions = {
    "python": ".py",
    "java": ".java",
}

TreeSitter_Languages = {
    "python": Language(tspython.language()),
    "java": Language(tsjava.language()),
}

Function_Types = {
    "python": {"function_definition"},
    "java": {"method_declaration", "constructor_declaration"},
}


def make_session(token: str | None = None):
    session = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Miner",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    session.headers.update(headers)
    return session


def search_repos(session, page: int = 1, per_page: int = 30):
    url = f"{Base_Url}/search/repositories"

    lang_query = ",".join(Languages)

    params = {
        "q": f"language:{lang_query} stars:>1",
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": per_page,
    }
    data = github_request(session, url, params=params)
    if data is None:
        return []
    return data.get("items", [])


def github_request(session, url, params):
    for attempt in range(1, Max_Attempts + 1):
        try:
            response = session.get(url, params=params, timeout=15)
        except requests.RequestException:
            wait(attempt)
            continue

        check_rate_limit(response)
        if response.status_code == 200:
            return response.json()
        elif response.status_code in (403, 429):
            wait(attempt)
        elif response.status_code == 422:
            return None
        elif response.status_code >= 500:
            wait(attempt)
        else:
            return None

    return None


def check_rate_limit(response):
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_at = response.headers.get("X-RateLimit-Reset")
    if remaining is None:
        return
    remaining = int(remaining)
    if remaining <= 5:
        reset_at = int(reset_at) if reset_at else time.time() + 60
        wait_seconds = max(0, reset_at - time.time()) + 5
        time.sleep(wait_seconds)


def wait(attempt):
    seconds = 2**attempt
    time.sleep(seconds)


def clone_repo(repo):
    full_name = repo["full_name"]
    clone_url = repo["clone_url"]
    dest = os.path.join(Temp_Folder, full_name)

    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)

    os.makedirs(dest, exist_ok=True)

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", clone_url, dest],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            shutil.rmtree(dest, ignore_errors=True)
            return None
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        return None
    except OSError:
        return None

    return dest


def delete_repo(path):
    shutil.rmtree(path, ignore_errors=True)
    parent = os.path.dirname(path)
    if os.path.isdir(parent) and not os.listdir(parent):
        shutil.rmtree(parent, ignore_errors=True)


def find_files(repo_path, language):
    ext = Extensions.get(language)
    if ext is None:
        return []

    found = []
    for dirpath, _, filenames in os.walk(repo_path):
        for filename in filenames:
            if filename.endswith(ext):
                found.append(os.path.join(dirpath, filename))
    return found


def extract_function_names(source_code, language):
    language = language.lower()
    if language not in TreeSitter_Languages:
        return []

    parser = Parser(TreeSitter_Languages[language])
    code_bytes = source_code.encode("utf-8", errors="ignore")

    try:
        tree = parser.parse(code_bytes)
    except Exception:
        return []

    results = []
    tree_read(tree.root_node, Function_Types[language], results)
    return results


def tree_read(node, target_types, results):
    if node.type in target_types:
        for child in node.children:
            if child.type == "identifier":
                results.append(child.text.decode("utf-8", errors="ignore"))
                break
    for child in node.children:
        tree_read(child, target_types, results)


def extract_words(function_name):
    if function_name.startswith("__") and function_name.endswith("__"):
        return []
    return split_name(function_name)


def split_name(name):
    name = name.replace("_", " ").replace("-", " ")

    built = ""
    for i, char in enumerate(name):
        if i > 0:
            prev = name[i - 1]
            if (prev.islower() or prev.isdigit()) and char.isupper():
                built += " "
            elif prev.isalpha() and char.isdigit():
                built += " "
            elif prev.isdigit() and char.isalpha():
                built += " "
            elif i > 1 and char.islower() and prev.isupper() and name[i - 2].isupper():
                built = built[:-1] + " " + prev
        built += char

    return [w.lower() for w in built.split() if len(w) > 1 and not w.isnumeric()]


def mine_repo(repo):
    repo_path = clone_repo(repo)
    if repo_path is None:
        return {lang: {} for lang in Languages}, 0, 0

    try:
        counts = {lang: defaultdict(int) for lang in Languages}
        total_files = 0
        total_functions = 0

        for language in Languages:
            files = find_files(repo_path, language)
            total_files += len(files)

            for filepath in files:
                process_file(filepath, language, counts[language])

            total_functions += sum(counts[language].values())

    finally:
        delete_repo(repo_path)

    return (
        {lang: dict(counts[lang]) for lang in Languages},
        total_files,
        total_functions,
    )


def process_file(filepath, language, counts):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()
    except OSError:
        return

    for name in extract_function_names(source_code, language):
        for word in extract_words(name):
            counts[word] += 1


# Main para probar
if __name__ == "__main__":
    # Si existe un token en el env, se ocupa, si no. pos no
    token = os.getenv("GITHUB_TOKEN")
    if token:
        print("Usando token")
    else:
        print("No token")

    session = make_session(token)

    print("Buscando repositorios")
    repos = search_repos(session, page=1, per_page=15)
    if not repos:
        print("No se encontraron repositorios.")

    for repo in repos:
        print(f"\n{repo['full_name']}({repo['stargazers_count']:,})")
        counts, total_files, total_functions = mine_repo(repo)
        print(f"Archivos:  {total_files}")
        print(f"Funciones: {total_functions}")
        for lang in Languages:
            words = counts.get(lang, {})
            if not words:
                continue
            top5 = sorted(words.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 palabras ({lang}): {top5}")
