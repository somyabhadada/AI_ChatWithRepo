import subprocess
import sys

def clone_repo(repo_url, destination_folder=None):
    try:
        # Build the command
        command = ["git", "clone", repo_url]
        if destination_folder:
            command.append(destination_folder)

        subprocess.run(command, check=True)
        print("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        print(" Error while cloning the repository:", e)
        sys.exit(1)

if __name__ == "__main__":
    repo_link = input("Enter the GitHub repository URL: ").strip()
    clone_repo(repo_link)
