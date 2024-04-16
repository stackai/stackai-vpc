################################################################################
# STACK AI AWS AMI BUILD SCRIPT
################################################################################
#
# !!!WARNING!!! This script has been tested with very specific commits. New developments may make this obsolete.
#

stackend_commit_hash="b5617d9439ff7cdae7cdfe57f5d2c601dc852c41"
stackweb_commit_hash="c28a7ecb3f3f6cb5543960dc75890d998a13ff63"

# PROMT THE USER TO ENTER THE EMAIL AND NAME
echo "Enter your github email and name"
read -p "GitHub Email: " your_gh_email
read -p "GitHub Name: " your_name

echo "your github email is $your_gh_email"

sudo mkdir /stackai
sudo chown -R $USER /stackai

# install docker and docker compose
sudo apt update

# setup docker apt repository
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# install docker
sudo apt-get -y install  docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# setup git
git config --global user.email "$your_gh_email"
git config --global user.name "$your_name"

# add git ssh key fingerprints and add them to known_hosts
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# create ssh key for github
ssh-keygen -t ed25519 -C "$your_gh_email" -f ~/.ssh/id_ed25519

# add ssh key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# adk the user to add the ssh key to github
echo "Add the following ssh key to your github account:"
cat ~/.ssh/id_ed25519.pub
# wait for the user to add the ssh key to github
read -p "Press enter to continue"

# test the connection
echo "testng connection to gh"
ssh -T git@github.com

# clone the onprem git repository
git clone git@github.com:stackai/stackai-onprem.git

# go to the stackai-onprem directory
cd stackai-onprem

# clone stackeb and stackend git repositories
git clone git@github.com:stackai/stackend.git
git clone git@github.com:stackai/stackweb.git


echo "WARNING: We are going to checkout the last commit at which the stackai-onprem was tested. This may not be the latest commit. If you want to build the latest commit, please press Ctrl+C and run the following command: git checkout main"
echo "WARNING: If you want to use the latest commit, the following steps may not work as expected."

# checkout the last commit at which the stackai-onprem was tested
cd stackend && git checkout $stackend_commit_hash
cd ../stackweb && git checkout $stackweb_commit_hash

# let the user know the next steps
cd ..
echo "The current user is going ot be addded to the docker group. You will need to logout and login again to be able to run docker commands without sudo. After that, follow the stackai-onprem/README.md file to build the stackai-onprem docker images."
sudo groupadd docker
sudo gpasswd -a $USER docker

# logout and login again
sudo pkill -KILL -u $USER