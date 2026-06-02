#RUN GhamYar Project
#RUN the All File
#Fish File For Run For Linux Users
#Hossein Hesari
#GitHub : https://github.com/Hossein-Hesari

echo "Run Project ..."
sudo apt install figlet
figlet "GHAM YAR"
echo "STARTING ..."
echo "Enter Your gap GPT API:"
read -l GAP_API
set -gx GAPGPT_API_KEY "$GAP_API"

python3 -m venv .venv
source .venv/bin/activate.fish

echo "Checking libs ..."

function check_lib
    if pip show $argv[1] &>/dev/null
        echo "$argv[1] Installed ✓"
    else
        echo "Installing $argv[1] ..."
        pip install -i https://mirror-pypi.runflare.com/simple $argv[1]
    end
end

check_lib flask
check_lib requests
check_lib dotenv

echo "Run Server ..."
python3 server.py
