import os
import shutil
import subprocess
import sys
import zipfile

import requests


def download_innoextract(output_path: str) -> None:
    response = requests.get("https://api.github.com/repos/dscharrer/innoextract/releases/latest")
    data = response.json()

    for asset in data["assets"]:
        file_name = asset["name"]
        if file_name.endswith("windows.zip"):
            response = requests.get(asset["browser_download_url"])
            file_path = f"{os.environ['TEMP']}\\{file_name}"

            with open(file_path, "wb") as file:
                file.write(response.content)

            with zipfile.ZipFile(file_path, "r") as file:
                file.extract("innoextract.exe", output_path)


def zip_folder(folder_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)  # preserve folder structure
                zipf.write(file_path, arcname)


def main() -> int:
    download_innoextract("C:\\Windows")

    response = requests.get("https://download.msi.com/uti_exe/gaming-gear/MSI-Center.zip")
    file_path = f"{os.environ['TEMP']}\\MSI-Center.zip"
    extract_path = f"{os.environ['TEMP']}\\MSI-Center"
    center_version = ""

    with open(file_path, "wb") as file:
        file.write(response.content)

    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(file_path, "r") as file:
        file.extractall(extract_path)

    for file in os.listdir(extract_path):
        if file.endswith(".exe"):
            center_version = file.strip("MSI Center_.exe")
            subprocess.call(["innoextract", f"{extract_path}\\{file}", "--output-dir", extract_path])

    center_appx_path = f"MSI%20Center_{center_version}_x64.appx"

    for file in os.listdir(f"{extract_path}\\app"):
        if file.endswith(".appxbundle"):
            with zipfile.ZipFile(f"{extract_path}\\app\\{file}", "r") as file:
                file.extract(center_appx_path, extract_path)

    center_sdk_path = "DCv2/Package/MSI%20Center%20SDK.exe"

    with zipfile.ZipFile(f"{extract_path}\\{center_appx_path}", "r") as file:
        file.extract(center_sdk_path, extract_path)

    subprocess.call(["innoextract", f"{extract_path}\\{center_sdk_path}", "--output-dir", extract_path])

    prepackage_path = f"{extract_path}\\tmp\\PrePackage"

    for file in os.listdir(prepackage_path):
        if "Engine Lib" in file:
            subprocess.call(["innoextract", f"{prepackage_path}\\{file}", "--output-dir", extract_path])

    scewin_path = f"{extract_path}\\app\\Lib\\SCEWIN"

    for folder in os.listdir(scewin_path):
        for file in ("BIOSData.db", "BIOSData.txt", "SCEWIN.bat"):
            try:
                os.remove(f"{scewin_path}\\{folder}\\{file}")
            except FileNotFoundError:
                pass

        for script in ("Import.bat", "Export.bat"):
            shutil.copy2(f"{script}", f"{scewin_path}\\{folder}")

    zip_folder(scewin_path, "SCEWIN.zip")

    return 0


if __name__ == "__main__":
    sys.exit(main())
