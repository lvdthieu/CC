import os
import pandas as pd
from settings import ROOTDIR


def organize_data():
    repos_path = os.path.join(ROOTDIR, "valid_repos.csv")
    repos = pd.read_csv(repos_path)
    error_log = open("error_log.txt", "a+")
    for repo in repos["Repo"]:
        if repo == "React"
        try:
            folder = repo.replace('/', '_')
            repo_path = os.path.join(ROOTDIR, "data", folder)
            print(repo)
            try:
                rn_info = pd.read_csv(os.path.join(repo_path, "rn_info.csv"))
                rn_info["published_at"] = pd.to_datetime(rn_info["published_at"])
                rn_info = rn_info.sort_values(by="published_at", ascending=False, ignore_index=True)
                rn_info.to_csv(os.path.join(repo_path, "rn_info_sorted.csv"), index=False)
            except Exception:
                raise Exception("Problem while sorting release note info")
            
            try:
                pr_info = pd.read_csv(os.path.join(repo_path, "pr_info.csv"))
                pr_info["created_at"] = pd.to_datetime(pr_info["created_at"])
                pr_info = pr_info.sort_values(by="created_at", ascending=False, ignore_index=True)
                pr_info.to_csv(os.path.join(repo_path, "pr_info.csv"), index=False)
            except Exception:
                raise Exception("Problem while sorting pull request info")

            try:
                issue_info = pd.read_csv(os.path.join(repo_path, "issue_info.csv"))
                issue_info["created_at"] = pd.to_datetime(issue_info["created_at"])
                issue_info = issue_info.sort_values(by="created_at", ascending=False, ignore_index=True)
                issue_info.to_csv(os.path.join(repo_path, "issue_info.csv"), index=False) 
            except Exception:
                raise Exception("Problem while sorting issue info")   
        except Exception as e:
            error_log.write(f"Repo {repo} encounter error: {e.message if hasattr(e, 'message') else e}\n")             
            continue    
    error_log.close()

    

        
        
        
            