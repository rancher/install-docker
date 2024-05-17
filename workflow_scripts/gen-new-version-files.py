import os
import subprocess
import semver

# Constants
DIST_FOLDER = './dist'
NEW_VERSIONS = os.environ.get("NEW_VERSIONS","")
SCRIPT_EXTENSION=".sh"

if NEW_VERSIONS == "":
    print("no new versions available, NEW_VERSIONS env variable is empty")
    exit(1)

def get_last_added_version(files_dir):
    max_modification_time = 0.0
    last_added_version = "0.0.0"
    for file in os.listdir(files_dir):
        if file.endswith(SCRIPT_EXTENSION) and file.count('.') == 3:
            file_path = os.path.join(files_dir, file)
            modification_time = os.path.getmtime(file_path)
            file_version = file.removesuffix(SCRIPT_EXTENSION)
            if modification_time > max_modification_time:
                max_modification_time = modification_time
                last_added_version = file_version
            elif modification_time == max_modification_time:
                last_added_version = semver.max_ver(last_added_version,file_version)

    return last_added_version

def generate_diffs(prev_version, current_version):
    print("executing add-new-version-script with PREVIOUS_ADD_DOCKER_VERSION: ",prev_version, 
    " ADD_DOCKER_VERSION",current_version)
    add_new_version_script_path = "./scripts/add-new-version"
    env_vars = {"PREVIOUS_ADD_DOCKER_VERSION": prev_version, "ADD_DOCKER_VERSION": current_version} 
    subprocess.run(["bash", add_new_version_script_path], check=True, env=env_vars)

# it will return a dictonary with key set to major.minor of a version and the
# value will be the greatest version for that major minor combination
def get_version_dict(versions):
    version_dict = {}

    for version in versions:
        version_parts = semver.parse(version)
        major_minor = f"{version_parts['major']}.{version_parts['minor']}"
        version_dict[major_minor] = semver.max_ver(version_dict.setdefault(major_minor, version), version)

    return version_dict

def main():

    last_added_version = get_last_added_version(DIST_FOLDER)
    print("Last added version:",last_added_version)
    
    version_list = [version.removeprefix('v') for version in NEW_VERSIONS.split(',')]
    print("Formatted new versions: ", version_list)

    for version in version_list:
        generate_diffs(last_added_version, version)

    print("running generate script")
    subprocess.run(["bash", "./scripts/generate"], check=True)

    version_dict = get_version_dict(version_list)
    print("version dictionary for symlink: ",version_dict)

    for major_minor,version in version_dict.items():
        subprocess.call(['rm',f"{DIST_FOLDER}/{major_minor}.sh"])
        os.symlink(f"{version}.sh",f"{DIST_FOLDER}/{major_minor}.sh")

if __name__ == "__main__":
    main()
