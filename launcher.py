import subprocess
import sys
import importlib.util
import main

def is_installed(package):
    spec = importlib.util.find_spec(package)
    return spec is not None

def install_requirements():
    missing_packages = []

    with open("requirements.txt", "r") as f:
        for line in f:
            package = line.strip().split("==")[0]
            if not is_installed(package):
                missing_packages.append(package)

    if missing_packages:
        print(f"Installing missing dependencies: {', '.join(missing_packages)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
    else:
        print("All dependencies are already installed.")

if __name__ == "__main__":
    install_requirements()  
    main.main() 
