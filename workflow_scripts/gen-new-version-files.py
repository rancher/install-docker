import os
import subprocess
import requests

# Constants
DIST_FOLDER = './dist'
NEW_VERSIONS = os.environ.get("NEW_VERSIONS","")

if NEW_VERSIONS == "":
    print("no new versions available, NEW_VERSIONS env variable is empty")
    exit(1)

def get_max_version(ver1, ver2):
    if ver1.startswith('v'):
        ver1 = ver1[1:]
    if ver2.startswith('v'):
        ver2 = ver2[1:]

    ver1_tuple = tuple(map(int, ver1.split('.')))
    ver2_tuple = tuple(map(int, ver2.split('.')))
    if ver1 > ver2:
        return ver1
    return ver2

def format_version(v):
    if v.startswith('v'):
        return v[1:]
    return v 

def get_last_added_version(files_dir):
    max_modification_time = 0.0
    last_added_version = ""
    for file in os.listdir(files_dir):
        if file.endswith('.sh') and file.count('.') == 3:
            file_path = os.path.join(files_dir, file)
            modification_time = os.path.getmtime(file_path)
            file_version = 'v' + file[:-3]
            if modification_time > max_modification_time:
                max_modification_time = modification_time
                last_added_version = file_version
            elif modification_time == max_modification_time:
                if last_added_version == "":
                    last_added_version = file_version
                else:
                    last_added_version = get_max_version(last_added_version,file_version)

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
        version_parts = version.split('.')
        major_minor = version_parts[0] + '.' + version_parts[1]
    
        if major_minor in version_dict:
            current_version = tuple(map(int, version_parts[2]))
            max_version = tuple(map(int, version_dict[major_minor].split('.')[2]))
            if current_version > max_version:
                version_dict[major_minor] = version
        else:
            version_dict[major_minor] = version

    return version_dict

def main():

    last_added_version = get_last_added_version(DIST_FOLDER)
    print("Last added version:",last_added_version)
    
    new_versions = NEW_VERSIONS.split(',')
    formatted_new_versions = list(map(format_version,new_versions))
    print("Formatted new versions: ", formatted_new_versions)

    for version in formatted_new_versions:
        generate_diffs(last_added_version, version)

    versions_string = ",".join(new_versions)

    print("running generate script")
    subprocess.run(["bash", "./scripts/generate"], check=True)

    version_dict = get_version_dict(formatted_new_versions)
    print("version dictionary for symlink: ",version_dict)

    for major_minor,version in version_dict.items():
        subprocess.call(['rm',f"{DIST_FOLDER}/{major_minor}.sh"])
        os.symlink(f"{version}.sh",f"{DIST_FOLDER}/{major_minor}.sh")

if __name__ == "__main__":
    main()
