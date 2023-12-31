""" Module provide functions to make data """
import os
import re
from typing import List, Callable, Tuple, TypeVar
import requests
import pygit2
import pandas as pd
from bs4 import BeautifulSoup
from markdown import markdown
from settings import ROOTDIR, HEADERS, VALID_RN_NUM, VALID_LINK_NUM, CM, PR, IS

Time = TypeVar("Time")
Markdown = TypeVar("Markdown")

class MyRemoteCallbacks(pygit2.RemoteCallbacks):
    """ Define function to show state of cloning process """
    def transfer_progress(self, stats):
        print(f'{stats.indexed_objects}/{stats.total_objects}')


def crawl_repos(result_path: str) -> None:
    """ Crawl Github repo with highest star number 
        (Assume that the higher star number the higher project quality) 
        Store result in result_path """

    result = []
    for i in range(50):
        print(i + 1)
        resp = requests.get(f"https://gitstar-ranking.com/repositories?page={i + 1}")
        soup = BeautifulSoup(resp.text, "html.parser")
        repos_container = soup.find("div", {"class": "row"})
        repos = repos_container.find_all('a')
        for repo in repos:
            result.append('/'.join(repo["href"].split('/')[-2:]))  
    result = pd.DataFrame({"Repo": result})
    result.to_csv(result_path)


def traverse_repos(repo_list_path: str, func: Callable[[str, str], None]) -> None:
    """ This function do func in range of all repositories in repo list file"""

    repos = pd.read_csv(repo_list_path)
    error_log = open("error_log.txt", "a+")
    for repo in repos["Repo"]:
        try:
            func(repo)
        except Exception as e:
            error_log.write((f"Repo {repo} encounter error: {e.message if hasattr(e, 'message') else e} "
                            f"in function {func.__name__}\n"))
    error_log.close()


def github_api(repo: str, component: str, func: Callable, params: str="") -> List[str]:
    """ Get all specific component of element has type is type using github_api """

    page = 1
    all_els = []
    while True:
        url =f"https://api.github.com/repos/{repo}/{component}?{params}&per_page=100&page={page}"
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except requests.HTTPError:
            if response.status_code == 422:
                break
            else:
                raise IOError("Http Error")
        except requests.Timeout:
            raise IOError("Timeout Error")
        els = response.json()
        els_per_page = [func(el) for el in els]
        all_els += els_per_page
        # 100 is the limit of per_page param in github api
        if len(els) < 100: 
            break
        page += 1

    return all_els


def crawl_rn(repo: str) -> Callable[[str, str, str, Callable], List[str]]:
    """ Crawl all release notes at repo"""

    print(repo)
    
    return github_api(repo, component="releases", func=lambda el: el)


def crawl_pr(repo: str) -> Callable[[str, str, str, Callable], List[str]]:
    """ Crawl all pull requests of repo """

    print(repo)
    
    return github_api(repo, component="pulls", params="state=all", func=lambda el: el)


def crawl_issue(repo: str) -> Callable[[str, str, str, Callable], List[str]]:
    """ Crawl all issues of repo """

    print(repo)

    return github_api(repo, component="issues", params="state=all", func=lambda el: el)


def crawl_cm(repo: str) -> List[str]:
    """ Crawl all commits in repo """

    folder = repo.replace('/', '_')
    path = os.path.join(ROOTDIR, "repos", folder)
    assert os.path.exists(path)
    cmd = f""" cd {path}
            git branch -a"""
    all_branches = os.popen(cmd).read().split('\n')[:-1]
    all_branches = [branch.strip() for branch in all_branches if "HEAD ->" not in branch]
    all_commit_shas = set()
    for branch in all_branches[1:]:
        try:
            cmd = f"""cd {path}
            git rev-list {branch}"""
            commit_shas = os.popen(cmd).read()
            # Each line is a commit sha and the last line is empty line
            commit_shas = commit_shas.split('\n')[:-1]
            all_commit_shas.update(commit_shas)
        except Exception:
            continue
    repo = pygit2.Repository(path)
    # Get commit message from commit sha
    commits = [repo.revparse_single(commit_sha) for commit_sha in all_commit_shas]
    # Get all commit message and commit sha
    commits = [
        {
            "message": commit.message, 
            "sha": commit.hex, 
            "author": commit.author, 
            "commit_time": commit.commit_time, 
            "committer": commit.committer
        }
        for commit in commits
    ]
    commits = pd.DataFrame(commits)
    return commits


def cm_spliter(message: str) -> Tuple[str, str]:
    """ Split commit into commit summary (the first line) and follow by commit description """

    try:
        # Convert markdown into html
        html = markdown(message)
        soup = BeautifulSoup(html, "html.parser")
        lines = [p.text.strip() for p in soup.find_all('p')]
        summary= lines[0]
        description = "<.> ".join(lines[1:])

        return summary, description
    except Exception:
        return None, None


def clone_repos(repo: str) -> None:
    """ Clone github repository """

    folder = repo.replace('/', '_')
    path = os.path.join(ROOTDIR, "repos", folder)
    if os.path.exists(path):
        return None
    print(repo)
    pygit2.clone_repository(f"https://github.com/{repo}", path, callbacks=MyRemoteCallbacks())


def build_rn_info(repo: str) -> None:
    """ Get information of release notes at repo and store into a csv file at data/[repo] """

    folder = repo.replace('/', '_')
    print("Repo:",repo)
    folder_path = os.path.join(ROOTDIR, "data", folder)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    rn_info_path = os.path.join(folder_path, "rn_info.csv")
    # Release note info path exists mean that this repo is processed so pass it
    if os.path.exists(rn_info_path):
        return None
    try:
        # Crawl changelogs
        print("Start crawl release notes")
        rn_info = crawl_rn(repo)
        print("Crawl release notes done")
        assert rn_info is not None
        rn_info = pd.DataFrame(rn_info)
        rn_info.to_csv(rn_info_path)
    except Exception as e:
        print("Wrong implement at build_rn_info")
        raise e


def build_cm_info(repo: str) -> None:
    """ Get information of commits at repo and store into a csv file at data/[repo] """

    folder = repo.replace('/', '_')
    print("Repo:", repo)
    folder_path = os.path.join(ROOTDIR, "data", folder)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    commit_path = os.path.join(folder_path, "commit.csv")
    # Commit path exists mean that this repo is processed so pass it
    # if os.path.exists(commit_path):
    #     return None
    try:
        print("Start load commits")
        commits = crawl_cm(repo)
        print("Commits loaded")
        assert commits is not None
        # Get commit messages and commit descriptions
        summa_des = [cm_spliter(commit)
                    for commit in commits.loc[:, "message"]]
        summaries, descriptions = zip(*summa_des)
        commit_df = pd.DataFrame({
            "Summary": summaries, 
            "Description": descriptions,
            "Sha": commits["sha"],
            "Author": commits["author"],
            "Committer": commits["committer"],
            "Commit Time": commits["commit_time"]
        })
        # Check commit messages
        print("Num commit messages:", len(commit_df))
        print("\n")
        print("==============================================")
        print("\n")
        commit_df.to_csv(commit_path)
    except Exception as e:
        print("Wrong implemen at build_cm_info function")
        raise e


def build_pr_info(repo: str) -> None:
    """ Get information of pull requests at repo and store into a csv file at data/[repo] """

    folder = repo.replace('/', '_')
    print("Repo:", repo)
    folder_path = os.path.join(ROOTDIR, "data", folder)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    pr_info_path = os.path.join(folder_path, "pr_info.csv")
    # Pull request info path exists mean that this repo is processed so pass it
    if os.path.exists(pr_info_path):
        return None
    try:
        # Crawl changelogs
        print("Start crawl pull requests")
        pr_info = crawl_pr(repo)
        print("Crawl pull requests done")
        assert pr_info is not None
        pr_info = pd.DataFrame(pr_info)
        pr_info.to_csv(pr_info_path)
    except Exception as e:
        print("Wrong implement at build_pr_info function")
        raise e


def build_issue_info(repo: str) -> None:
    """ Get information of release notes at repo and store into a csv file at data/[repo] """

    folder = repo.replace('/', '_')
    print("Repo",repo)
    folder_path = os.path.join(ROOTDIR, "data", folder)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    issue_info_path = os.path.join(folder_path, "issue_info.csv")
   
    # Issue info path exists mean that this repo is processed so pass it
    if os.path.exists(issue_info_path):
        return None
    try:
        # Crawl changelogs
        print("Start crawl issues")
        issue_info = crawl_issue(repo)
        print("Crawl issues done")
        issue_info = pd.DataFrame(issue_info)
        issue_info.to_csv(issue_info_path)
    except Exception as e:
        print("Wrong implement at build_issue_info function")
        raise e


def make_data() -> None:
    """ This function define a pipeline to get data from top repositories in Github (sort by stars) that statisfy
        some rule for specific problem """

    # crawl_repos("raw_repos.csv")
    # traverse_repos("valid_repos.csv", clone_repos)
    # traverse_repos("valid_repos.csv", build_rn_info)
    # traverse_repos("valid_repos.csv", build_cm_info)
    # traverse_repos("valid_repos.csv", build_pr_info)
    # traverse_repos("valid_repos.csv", build_issue_info)
