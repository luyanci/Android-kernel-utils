import os
import sys
import time
import requests
from loguru import logger
from tqdm.rich import tqdm

manual_hook_patches={
    "4.9": {"method":"git am","link":"https://github.com/xiaomi-msm8953-devs/android_kernel_xiaomi_msm8953/commit/27f273b.patch"},
    "4.14": {"method":"git am","link":"https://github.com/xiaomi-sdm678/android_kernel_xiaomi_mojito/commit/60e003b.patch"},
    "4.19": {"method":"git am","link":"https://github.com/alternoegraha/kernel_xiaomi_sm6225/commit/2eee8ac.patch"},
    "5.4": {"method":"git am","link":"https://github.com/dev-sm8350/kernel_oneplus_sm8350/commit/583337f.patch"},
    "GKI2": {"method":"patch","link":"https://github.com/ShirkNeko/SukiSU_patch/raw/main/hooks/syscall_hooks.patch"},
}

susfs_supported={"gki2":['android12-5.10','android13-5.10','android13-5.15','android14-5.15','android14-6.1','android15-6.6'],
                 "non-gki":['4.9','4.14','4.19','5.4']}

def get_kernel_versions():
    version=""
    patchlevel=""
    sublevel=""

    try:
        with open("Makefile",'r') as file:
            for line in file:
                if line.startswith("VERSION"):
                    version = line.split('=')[1].strip()
                elif line.startswith("PATCHLEVEL"):
                    patchlevel = line.split('=')[1].strip()
                elif line.startswith("SUBLEVEL"):
                    sublevel = line.split('=')[1].strip()
                elif line.startswith("#"): # skip comments
                    continue
                else:
                    break
    except FileNotFoundError:
        logger.error("MakeFile Not Found!")
        raise
    logger.info(f"Kernel version: {version}.{patchlevel}.{sublevel}")
    if (int(version) >= 5 and int(patchlevel) >= 10) or int(version) >= 6: # GKI2 detect
        logger.info("Kernel version is GKI2!")
        return "GKI2"
    return [version,patchlevel,sublevel]

def get_kmi():
    try:
        with open("build.config.common") as file:
            for line in file:
                if line.startswith("BRANCH"):
                    return line.split('=')[1].strip()
                else:
                    continue
    except FileNotFoundError:
        logger.error("build.config.common Not Found!")
        raise
    
def get_patches():
    kernel_ver=get_kernel_versions()
    if not kernel_ver == "GKI2": # if not GKI2
        kernel_ver=kernel_ver[0]+"."+kernel_ver[1]
    try:
        patches=manual_hook_patches[kernel_ver]
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        raise
    return patches

def downloader(url:str,filename:str):
    r=requests.get(url=url,stream=True,allow_redirects=True)
    if r.status_code == 200:
        size=int(r.headers.get("content-length"))
        bar=tqdm(total=size,unit='iB',unit_scale=True,desc=f"Downloading {filename}...")
        with open(filename,'wb') as file:
            for chunk in r.iter_content(chunk_size=1024*10):
                file.write(chunk)
                bar.update(len(chunk))
                bar.refresh()
            bar.close()
            file.close()

def download_patches(patches:dict):
    logger.info(f"Downloading patches from {patches['link']}")
    if os.path.exists('kernelsu.patch'):
        os.remove('kernelsu.patch')
    downloader(patches["link"],"kernelsu.patch")

def check_git_folder():
    if os.path.exists(".git") and os.path.isdir(".git"):
        logger.info("Git folder found!")
        return True
    else:
        logger.info("Git folder not found!")
        return False

def apply_patches(patches:dict):
    git_avaliable = check_git_folder()
    if patches['method'] == "git am" and git_avaliable:
        logger.info("Applying patch by git am...")
        os.system("git am kernelsu.patch")
    elif patches['method'] == "patch" or not git_avaliable:
        logger.info("Applying patch by patch...")
        os.system("patch -p1 < kernelsu.patch")
    else:
        logger.error("Unknown method!")
        raise ValueError("Unknown method!")
        
def get_susfs_repo():
    branch=""
    kernel_ver=get_kernel_versions()
    if kernel_ver == "GKI2":
        kernel_ver=get_kmi()
        if kernel_ver in susfs_supported['gki2']:
            branch=f"gki-{kernel_ver}"
        else:
            raise ValueError("Kernel version not supported")
    else:
        kernel_ver=kernel_ver[0]+"."+kernel_ver[1]
        if kernel_ver in susfs_supported['non-gki']:
            branch=f"kernel-{kernel_ver}"
        else:
            raise ValueError("Kernel version not supported")

    logger.info("Cloneing...")
    os.chdir(f"{os.getcwd()}/..")
    os.system(f"git clone https://gitlab.com/simonpunk/susfs4ksu -b {branch}")


def main():
    if "--get-susfs" in sys.argv:
        logger.info("Getting susfs...")
        get_susfs_repo()
    else:
        logger.info("Getting manual hook patches...")
        patches=get_patches()
        download_patches(patches)
        apply_patches(patches)


if __name__== "__main__": 
    s=time.perf_counter()
    logger.warning("Exprimental Project! It is on your risk!")
    main()
    logger.info(f"Done in {time.perf_counter()-s :0.2f} seconds!")
    