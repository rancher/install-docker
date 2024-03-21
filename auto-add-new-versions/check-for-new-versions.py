import os
import subprocess
import requests

# Constants
DIST_FOLDER = './dist'
EXCLUDED_VERSIONS = os.environ.get('EXCLUDED_VERSIONS', 'v20.10.x,v23.0.x')

def get_excluded_version_patterns(excluded_ver_str):
    excluded_ver_list = excluded_ver_str.split(',')
    excluded_patterns = []
    for ver in excluded_ver_list:
        ver_parts = ver.split('.')
        if len(ver_parts) == 3:
            if ver_parts[1] == 'x':
                excluded_patterns.append(ver_parts[0])
            elif ver_parts[2] == 'x':
                excluded_patterns.append(ver_parts[0] + '.'+ ver_parts[1])
            else:
                excluded_patterns.append(ver)
    return excluded_patterns


def is_excluded_version(excluded_patterns,version):
    for pattern in excluded_patterns:
        if version.startswith(pattern):
            return True
    return False

def get_existing_versions(files_dir):
    existing_versions = set()
    for file in os.listdir(files_dir):
        if file.endswith('.sh') and file.count('.') == 3:
            existing_versions.add('v' + file[:-3])
    return existing_versions

def fetch_ten_latest_github_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        releases = [release for release in response.json() if not release.get('prerelease')]
        return sorted(releases, key=lambda x: x['created_at'], reverse=True)[:10]
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch releases: {e}")
        return None

def get_version_tuple(version):
    if version.startswith('v'):
        version = version[1:]
    return tuple(map(int, version.split('.')))

def main():
    excluded_ver_patterns = get_excluded_version_patterns(EXCLUDED_VERSIONS)
    existing_versions = get_existing_versions(DIST_FOLDER)
    owner = "moby"
    repo = "moby"
    ten_latest_releases = fetch_ten_latest_github_releases(owner, repo)
    ten_latest_versions = [release['tag_name'] for release in ten_latest_releases]
    print("Ten latest versions: ",ten_latest_versions)

    new_versions = set(ten_latest_versions) - existing_versions
    new_versions = list(filter(lambda ver: not is_excluded_version(excluded_ver_patterns,ver),new_versions))

    sorted_new_versions = sorted(new_versions,key=get_version_tuple)
    print('New versions: ',sorted_new_versions)

    versions_string = ",".join(sorted_new_versions)
    PR_TITLE = ""
    
    if versions_string != "":
        PR_TITLE = "[Auto] Add docker " + versions_string
        print('PR Title: ', PR_TITLE)

    env_file = os.getenv('GITHUB_ENV')

    if env_file:
        with open(env_file, "a") as envfile:
            envfile.write("PR_TITLE="+PR_TITLE+"\n")
            envfile.write("NEW_VERSIONS="+versions_string+"\n")
    else:
        exit(1)



if __name__ == "__main__":
    main()
