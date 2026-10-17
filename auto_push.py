import git
import datetime

def sync_to_github(commit_message=None):
    try:
        repo = git.Repo(".")
        repo.git.add(A=True)
        
        if not commit_message:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto-sync at {now}"
            
        repo.index.commit(commit_message)
        print(f"✅ Committed: '{commit_message}'")
        
        origin = repo.remote(name='origin')
        origin.push()
        print("🚀 Automatically pushed to GitHub!")
    except Exception as e:
        print(f"⚠️ Git Sync Note: {e}")

if __name__ == "__main__":
    sync_to_github("Testing auto-push script")