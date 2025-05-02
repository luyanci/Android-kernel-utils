import os
import requests
from loguru import logger
from tqdm.rich import tqdm
import res

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


def get_patches():
    kernel_ver=get_kernel_versions()
    if not kernel_ver == "GKI2": # if not GKI2
        kernel_ver=kernel_ver[0]+"."+kernel_ver[1]
    try:
        patches=res.patches[kernel_ver]
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        raise
    return patches

def download_patches(patches:dict):
    logger.info(f"Downloading patches from {patches['link']}")
    if os.path.exists('kernelsu.patch'):
        os.remove('kernelsu.patch')
    r=requests.get(url=patches['link'],stream=True)
    if r.status_code == 200:
        size=int(r.headers.get("content-length"))
        bar=tqdm(total=size,unit='iB',unit_scale=True,desc="Downloading Patches...")
        with open('kernelsu.patch','wb') as file:
            for chunk in r.iter_content(chunk_size=1024*3):
                file.write(chunk)
                bar.update(len(chunk))
                bar.refresh()
            bar.close()
            file.close()

def apply_patches(patches:dict):
    logger.info(f"Applying patches by {patches['method']}...")    
    if patches['method'] == "git am":
        os.system("git am kernelsu.patch")
    elif patches['method'] == "patch":
        os.system("patch -p1 < kernelsu.patch")
    else:
        logger.error("Unknown method!")
        raise ValueError("Unknown method!")
        

if __name__== "__main__":
    logger.warning("Exprimental Project! It is on your risk!")
    patches=get_patches()
    download_patches(patches)
    apply_patches(patches)
    logger.info("Done!")
    