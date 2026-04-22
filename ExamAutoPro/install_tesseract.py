import os
import urllib.request
import zipfile
import subprocess
import sys

def install_tesseract():
    """Download and install Tesseract OCR for Windows"""
    
    print("Installing Tesseract OCR...")
    
    # Tesseract download URL
    tesseract_url = "https://github.com/UB-Mannheim/tesseract/wiki/tesseract-ocr-w32-setup-5.4.0-20240603.exe"
    
    # Download path
    download_path = os.path.join(os.getcwd(), "tesseract_setup.exe")
    
    try:
        # Download Tesseract installer
        print("Downloading Tesseract installer...")
        urllib.request.urlretrieve(tesseract_url, download_path)
        
        # Install silently
        print("Installing Tesseract...")
        subprocess.run([download_path, "/S"], check=True)
        
        # Add to PATH
        tesseract_path = r"C:\Program Files\Tesseract-OCR"
        if tesseract_path not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + tesseract_path
        
        print("Tesseract installation completed!")
        
        # Clean up
        if os.path.exists(download_path):
            os.remove(download_path)
            
        return True
        
    except Exception as e:
        print(f"Error installing Tesseract: {e}")
        print("Please install Tesseract manually from: https://github.com/UB-Mannheim/tesseract/wiki")
        return False

if __name__ == "__main__":
    install_tesseract()
