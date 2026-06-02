#RUN GhamYar Project
#RUN the All File
#Bash File For Run For Linux Users
#Hossein Hesari
#GitHub : https://github.com/Hossein-Hesari

echo "Run Project ..."
sudo apt install figlet
figlet "GAM YAR"
echo "STARTING ..."
echo "Enter Your gap GPT API:"
read GAP_API
export GAPGPT_API_KEY="$GAP_API"

python3 -m venv .venv
source .venv/bin/activate

echo "Checking libs ..."

check_lib() {
    if pip show "$1" &>/dev/null; then
        echo "$1 Installed ✓"
    else
        echo "Installing $1 ..."
        pip install -i https://mirror-pypi.runflare.com/simple "$1"
    fi
}

check_lib flask
check_lib requests
check_lib dotenv

echo "Run Server ..."
python3 server.py
