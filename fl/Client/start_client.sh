pip install -r requirements_client.txt

pip install gdown
if [ ! -f ECG5000 ]; then
    gdown --id 16MIleqoIr1vYxlGk4GKnGmrsCPuWkkpT
    sudo apt install unzip
    mkdir ECG5000
    unzip -qq ECG5000.zip -d ECG5000
fi

rm ECG5000.zip
python3 Client.py
