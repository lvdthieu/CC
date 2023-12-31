import os
import pandas as pd
from settings import ROOTDIR

def organize_data():
    repos_path = os.path.join(ROOTDIR, "valid_repos.csv")
    repos = pd.read_csv(repos_path)
    error_log = open("error_log.txt", "a+")
    for repo in repos["Repo"]: 
        try:
            folder = repo.replace('/', '_')
            repo_path = os.path.join(ROOTDIR, "data", folder)
            print(repo)
            # try:
            #     cm_info = pd.read_csv(os.path.join(repo_path, "commit.csv"))
            #     cm_info = cm_info.sort_values(by="Commit Time", ascending=False, ignore_index=True)
            #     cm_info.to_csv(os.path.join(repo_path, "commit_sorted.csv"), index=False)
            # except Exception:
            #     raise Exception("Problem while sorting commit info")
            # try:
            #     rn_info = pd.read_csv(os.path.join(repo_path, "rn_info.csv"))
            #     rn_info["published_at"] = pd.to_datetime(rn_info["published_at"])
            #     rn_info = rn_info.sort_values(by="published_at", ascending=False, ignore_index=True)
            #     rn_info.to_csv(os.path.join(repo_path, "rn_info_sorted.csv"), index=False)
            # except Exception as e:
            #     print(e.message)
            #     raise Exception("Problem while sorting release note info")
        
            # try:
            #     file_path = os.path.join(repo_path, "pr_info_sorted.csv")
            #     if os.path.exists(file_path):
            #         continue
            #     try:
            #         pr_info = pd.read_csv(os.path.join(repo_path, "pr_info.csv"), dtype="object")
            #     except Exception:
            #         pr_info = pd.read_csv(os.path.join(repo_path, "pr_info.csv"), 
            #                               dtype="object", engine="python", on_bad_lines="skip")
            #     pr_info["created_at"] = pd.to_datetime(pr_info["created_at"], errors="ignore")
            #     pr_info = pr_info.sort_values(by="created_at", ascending=False, ignore_index=True)
            #     pr_info.to_csv(file_path, index=False)       
            # except Exception as e:
            #     raise e
            
            try:
                file_path = os.path.join(repo_path, "issue_info_sorted.csv")
                if os.path.exists(file_path):
                    continue
                try:
                    issue_info = pd.read_csv(os.path.join(repo_path, "issue_info.csv"), dtype="object")
                except Exception:
                    issue_info = pd.read_csv(os.path.join(repo_path, "issue_info.csv"), 
                                          dtype="object", engine="python", on_bad_lines="skip")
                issue_info["created_at"] = pd.to_datetime(issue_info["created_at"], errors="ignore")
                issue_info = issue_info.sort_values(by="created_at", ascending=False, ignore_index=True)
                issue_info.to_csv(file_path, index=False)       
            except Exception as e:
                raise e
        except Exception as e:
            error_log.write(f"Repo {repo} encounter error: {e.message if hasattr(e, 'message') else e}\n")             
            continue    
    error_log.close()
        
            
