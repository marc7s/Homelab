# What is this project?
## What does it provide?
This project provides a way to provision a server running Proxmox for use in a homelab, that can have the following:
* A TrueNAS Scale instance
* Any docker containers of your choice, with Portainer to manage or monitor them. It has built in support for a development and production environment. Examples of what you could use them for:
  * Hosting static HTML or PHP websites
  * Cloudflare tunnels
  * Cloudflare DDNS
  * Running databases
* A Home Assistant instance
* A [Homer](https://github.com/bastienwirtz/homer) homepage for your homelab, which you can easily configure as a landing page with all the links you need to your different programs or machines

In short, you can define the containers, programs, virtual machines etc that you want to have on your server as code files, and then easily deploy it all to the server using this project.

## What do I need to create my homelab using this project?
A server running Proxmox is all you really need. You will also need a separate computer which will act as your Ansible control node. The Ansible controle node has to be a UNIX-like system, such as a Linux computer, Mac, or Windows using WSL. You can read the [official docs](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#control-node-requirements) if you are unsure. Installing Proxmox will be explained later in this guide, and for the server it could be a dedicated rack mounted server with enterprise parts or an old laptop, it all depends on what you have and what you need. One of the great things with this project is that if you start on some hardware to try it out, and later want to upgrade your homelab, you can redeploy your setup to a new machine using the tools this project provides.

## Why did I create it?
This project was built to define my homelab server using IaC, or [Infrastructure as Code](https://www.redhat.com/en/topics/automation/what-is-infrastructure-as-code-iac). This allows me to manage and provision my homelab server (and in the future, *servers*) through code and scripts, which has a few benefits. Mainly in my case:
1. A sort of backup that makes sure that even if my server were to burn down, I could buy a new one, and get it up and running exactly like the old one simply by performing a few manual steps in combination with the scripts in this project
2. A good way of documenting (and automating) all those small things you do to get something working the first time - changing permissions, editing configuration files, creating users, enabling system features etc - and then forget about since you never touch it again and forget to write down what you did
3. A robust and automated deployment pipeline for hosting my projects, so that I have a separate development environment where I will not affect the stability or uptime of the production environment, and once I want to release a new version an automated production deployment for easier and quicker updates

## Why is this public?
As I started developing more and more features, I started to get the idea of providing others with a simple way to set up their homelab with commonly used programs and features through IaC. I would like to share all the experience I gained and the time I put into this project with others, as I could never find something like this and had to go through all the articles, documentation and trial and error from scratch. That made me separate my own homelab from this project, so that my own homelab would be a replacable module used as configuration for the scripts. That would allow others to create their own homelabs with whatever they need to have by defining their own such module, while still using the same code to make it all happen. So I still use this repository for my homelab, but that configuration is hidden as it is my personal setup.

## How does it work?
In short, [Ansible](https://www.ansible.com/overview/how-ansible-works) is an open source tool for provisioning systems, deploying software, updating systems and much more. By creating Ansible scripts, called *Playbooks*, you can do all these things with an important difference from just creating scripts in `bash`, `Powershell` or alike: it is idempotent. Idempotence means that running the same script multiple times, yields the same result in the end. As an example, if one of your tasks is to add an SSH key to the `authorized_keys` file (append a string to a file), a normal script would add the same key again even if it has already been added (unless you specifically check for it). However, Ansible would only add that key if it is not already added, otherwise that task will be skipped. Since Ansible it built upon idempotency, you do not have to perform all these duplication checks and can rerun setup scripts without issues. This makes it perfect for something like this, as you rather define the end result you would like to accomplish instead of what changes to make as in a traditional shell script.

The Ansible playbooks read from the `Configuration/` folder where you put the configuration for your own Homelab, and uses that to configure the server, deploy your applications and so on. Playbooks can also import *roles*, similar to *functions* in programming, where you can define several tasks in a role such as deploying a docker container. Then you can import that role with different parameters to deploy several docker containers.

# Explaining the project
## The structure
The configuration for your homelab is stored in the gitignored `/Configuration` folder, which should have the same structure as the `/ConfigurationExample` folder. To version control your homelab IaC, initialize a repository inside the `/Configuration` folder, and then copy the contents of `/ConfigurationExample` into there. Then, it is time to customize your homelab. You can use the `/ConfigurationExample` structure and files to understand how to create your homelab through IaC, just be mindful that any files ending in `.vault` **should be encrypted using Ansible Vault**, and not be plain text files. In the example folder, they are plain text files so you can see the contents, but you should instead use `ansible-vault` to create such files as will be explained later.

On the remote homelab server: any repositories will be placed in the `/Repos` folder, while this repository will be placed inside the `/Homelab` folder. Any files used for deployment will be placed in the `/Deploy` folder. Although there are exceptions, in general DEV containers will use a bind mount to the repository for accessing the project files, so you can develop in live mode where changes will immediately affect the running container. In contrast, PROD containers will build once deployed, and store the files inside the container.

To keep everything organized, ports are placed in the `Configuration/group_vars/all/ports.yml` file. This allows you to keep all ports in one single file, allowing you to easily change them while looking for potential clashes. You can then reference those in your docker compose files with templating. To ensure you do not have any port clashes, you can run the `ansible-playbook setup/validate-port-clashes.yml` command to automatically check for port clashes, as long as it has the same type of structure as the example ports file.

## Static data and configs for containers
The `Containers` folder contains any data for your containers that you want version controlled. For example, [Homer](https://github.com/bastienwirtz/homer) is an easy to configure homepage for your homelab. A `Homer` directory can be used as in the example to keep your `Homer` homepage version controlled. If you want to update your homelab homepage, you can simply edit the `config.yml` file inside the `Homer` folder to modify your homepage. You will not see any files inside this directory from the start, but once you start the `Homer` container, it will generate the files for you. Then you can edit them. *Note:* you do not want any dynamic data in here as that will generate changes to your repository every time the container changes those files. `Homer` only reads from that folder, it does not write to it which means that it is a good fit for the `Containers` folder use case.

## Docker container configuration
**Note: The deployment is based on Docker Compose V2.**

The `docker` folder contains all the configurations for your containers. Create a new folder inside here if you want a new container. Inside your container subfolder, you can put a `.env.prod.vault` or `.env.dev.vault` file as in the example, **HOWEVER** you should use encrypt these files so you do not have secrets in plain text, especially since you probably want to push your code to GitHub (even though in a private repository). As an example, for the `FullStackWebApp` example, you can run `ansible-vault create Configuration/docker/FullStackWebApp/Backend/.env.dev.vault` and enter your environment variables in that file. The files in the `ConfigurationExample` folder are *unencrypted for transparency*, but you should not reuse those files, instead use `ansible-vault` as explained to encrypt the files. But make sure you follow the name convention as seen in the `ConfigurationExample` folder, as the deployment scripts will look for files following that name convention.

Moving on to the actual containers, put your docker compose files inside that same folder, as seen in the `FullStackWebApp` example with the two compose files `fullstackwebapp-backend.dev.yml` and `fullstackwebapp-backend.prod.yml` for the two different environments.

## General instructions for configuration
You can customize your homelab by creating your own Ansible deployment scripts or docker composes, all in the `Configuration/` folder, where you will still have access to tools from the main repository such as the deployment roles in `/deploy/roles`. This will allow you to use this repository as a library for your own scripts, but also for instructions or examples. By having your own data inside the ignored `Configuration/` folder, you will still be able to pull the latest changes for new functionality or bug fixes, all while keeping your own Homelab IaC in your own private repository.

Many commands, files you have to create or instructions contain some data that needs to be replaced. An example might be the following line in a file:
```yml
favourite_fruit: YOUR_FRUIT_HERE
fruit_colour: 'YOUR_COLOUR_HERE'
```
As all homelabs differ, the values in my case might be *apple* and *green*, but in your case it could be *banana* and *yellow*. Always read the instructions carefully and be aware of special characters such as quotes. In your file, you would therefore put:
```yml
favourite_fruit: banana
fruit_colour: 'yellow'
```

Always read the instructions carefully as you often need to replace values with your own

# Setup
The first step is to clone this repository to your machine that you will use as your Ansible control node. As explained earlier, this can be any UNIX-like machine, or a Windows machine using WSL. 

For Windows users, you will be using WSL so continue reading to learn how to set it up.

For non-Windows users, you will also need an editor for configuring your repository. I strongly recommend VS Code, which for Windows users comes preinstalled through WSL, otherwise I would install VS Code before continuing with this guide.

**If you are not on Windows, skip the next section and instead continue reading [the following section](#setting-up-this-repository)**.

## For Windows users - Setting up WSL
Since Ansible does not have Windows support, the easiest solution is to set everything up in WSL (Windows Subsystem for Linux). WSL will act as your Ansible control node, which is the host from which you execute the scripts. Any mention of Ansible control node, will therefore refer to the WSL instance in this case.

1. Install WSL, either through command line or through the Windows Store. Note that virtualization needs to be enabled in the BIOS
2. Open the WSL terminal
3. Set up [Git Credential Manager](https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-git#git-credential-manager-setup), the command depends on your Git version
4. Choose a root password for WSL by following [the WSL documentation](https://learn.microsoft.com/en-us/windows/wsl/setup/environment#set-up-your-linux-username-and-password)
5. Run `sudo nano /etc/wsl.conf`
6. Add the following:
```
[boot]
systemd=true
```
7. Restart WSL by closing any instances of WSL, and then running `wsl.exe --shutdown` in `cmd.exe`

The rest of the installation process will be carried out through the WSL terminal, and the development and usage of Ansible will be carried out through the VS Code instance opened in WSL.

## Setting up this repository
Run the following commands in the terminal:
1. `cd ~`
2. `mkdir Repos`
3. `cd Repos`
4. `git clone https://github.com/marc7s/Homelab.git`
4. `cd Homelab`
5. `chmod o-w .`

The last step is due to Ansible not liking config files in world writable folders (777 permissions).

Next, you can open the repository by running `code .` while still inside the `Repos/Homelab` folder.

### Installing Ansible prerequisites
In order for Ansible to work, we need to install some prerequisites. Run the following commands in the terminal:
1. Installing python:
  1. `sudo apt update && upgrade`
  2. `sudo apt install python3 python3-pip ipython3`
2. Installing pipx:
  1. `python3 -m pip install --user pipx`
  2. `python3 -m pipx ensurepath`
3. Adding a preferred editor:
  1. `nano ~/.bashrc`
  2. Go to the bottom of the file and add this line: `export EDITOR=nano` to use nano
  3. Save the file
4. Restart your computer

### Creating your private homelab configuration repository
Next, you will need to create a new private repository to store your own homelab configuration. To do this, create an empty folder named `Configuration` at the root level of this repository, so that it is a sibling to the `ConfigurationExample` folder. Then, go inside that folder and initialize a new repository. To store your configuration privately on GitHub (which can act as a cloud backup of your homelab, excluding the ignored files), create a new private repository on GitHub and set that repository as the remote for the newly created repository inside the `Configuration` folder. Make sure that any files you place inside this private repository are directly inside the `Configuration` folder of this repository. For example, if you create a `README.md` file on the root level of your private repository, the relative path to that file should be `Homelab/Configuration/README.md`.

Next, copy **the contents** of the `ConfigurationExample` folder, *without copying the folder itself*, so that the `Configuration/` folder exactly matches the `ConfigurationExample` folder. You will modify your configuration at a later stage.

## Keyword clarification
To follow the instructions, you need to give your homelab server a name. In the instructions, I will refer to it as `homelabservername`. Any time you see this, you should replace it with the name of your homelab. I have not tested it, but names containing spaces should be fine but I would recommend against it. Instead I would use a lower case name without spaces or special characters.

In the same fashion, the "Configuration repository" refers to your private repository placed inside `Configuration/`, that contains your own homelab definition. If you name that repository `HomeLabConfiguration`, then "Configuration repository name" would be `HomeLabConfiguration`.

At the moment, it walks you through every step, but if your homelab looks different (for example you do not want TrueNAS, or Home Assistant) you have to be creative when reading and skip those specific steps.

Otherwise, I would urge you to follow the instructions exactly as they are, since there are scripts that depend on you having set everything up in a precise way, with certain folder structures with specific names and so on.

## Installing Proxmox
1. Install Proxmox, I used Proxmox VE 8.0.3. [Download](https://www.proxmox.com/en/downloads). Use a tool like [Rufus](https://rufus.ie/) to get the ISO to a USB.
2. Follow the installation wizard to set it up. Set the hostname (FQDN) to `homelabservername.local`. [Reference](https://www.youtube.com/watch?v=sZcOlW-DwrU)
3. Connect to Proxmox at `PROXMOX_IP_HERE:8006`, replacing with the IP the server got (check your router), log in with `root` and the password you set.

## Setting up a 10G NIC
If you have a separate Network Interface Card, such as a 10 Gbit network card that you would like your TrueNAS Scale instance to use for fast transfer speeds, follow the next steps. **If you do not have a separate NIC**, edit the `Configuration/group_vars/homelab_proxmox/vars.yml` and change the `network_bridge` value to `vmbr0`, which is the default network bridge.

If it is not a 10G NIC, you might have to modify the following instructions a bit to fit your situation.
1. In Proxmox, open the shell and run the following command: `dmesg | grep ixgbe`
2. That should show you the 10G NIC. Make a note of the MAC Address, you will need it in the next step
3. Follow the next steps [in the next section](#configuring-reliable-networking). Name the network device name "vmbr10" and make sure that matches with your `network_bridge` setting in the `Configuration/group_vars/homelab_proxmox/vars.yml` file

## Configuring reliable networking
Network interfaces might change if you reconfigure your server, as the names are generated, see [the documentation under the section Systemd Network Interface Names](https://pve.proxmox.com/wiki/Network_Configuration). To combat this, we set up links binding the MAC address of each NIC to a specific network interface name.

For each NIC, assign it a number 1-99. I will call this number NID. Then, under `/etc/systemd/network`, create a new file for each NIC named `NID-ethX.link`, where NID is the number you assigned and X is the identifier for the network device name. In the file, put the following:

```
[Match]
MACAddress=aa:bb:cc:dd:ee:ff

[Link]
Name=ethX
```
entering the MAC address of that NIC, and the corresponding network device name as the link name.

Then, update the network configuration to reference these interfaces, which is located under `/etc/network/interfaces`.

For example, if you have a built in 1Gbit port in the motherboard of the server with the MAC address `aa:aa:aa:aa:aa:aa` you wish to assign the name `eth1`, and a separate 10Gbit NIC with the MAC address `bb:bb:bb:bb:bb:bb` you with to assign the name `eth10`, you would run the following commands:

1. `nano /etc/systemd/network/1-eth1.link`
Content:
```
[Match]
MACAddress=aa:aa:aa:aa:aa:aa

[Link]
Name=eth1
```
2. `nano /etc/systemd/network/10-eth10.link`
Content:
```
[Match]
MACAddress=bb:bb:bb:bb:bb:bb

[Link]
Name=eth10
```
3. `nano /etc/network/interfaces`
Content:
```
...
iface eth1 inet manual
iface eth10 inet manual

auto vmbr0
iface vmbr0 inet static
        ...
        bridge-ports eth1
        ...

auto vmbr10
iface vmbr10 inet manual
  bridge-ports eth10
  bridge-stp off
  bridge-fd 0
```

## Preparing TrueNAS Scale and Docker
1. [Download](https://www.truenas.com/download-truenas-scale/) the TrueNAS Scale ISO that you want, and then go into `Configuration/group_vars/homelab_proxmox/vars.yml` and update the name of the ISO file for the TrueNAS Scale config, making sure it exactly matches the name of the ISO file (including the `.iso` file extension)
2. Upload the ISO to Proxmox through `Datacenter -> homelabservername -> local -> ISO Images -> Upload` and select the TrueNAS Scale ISO file
3. [Download](https://www.debian.org/download) a Debian ISO that you want and then go into `Configuration/group_vars/homelab_proxmox/vars.yml` and update the name of the ISO file for the Docker config, making sure it exactly matches the name of the ISO file (including the `.iso` file extension)
4. Upload the ISO to Proxmox through `Datacenter -> homelabservername -> local -> ISO Images -> Upload` and select the Docker ISO file

## Setting up the SSH connection to the Proxmox server
1. On the host computer (the control node, from which you will run the Ansible scripts), generate a new SSH key by running `ssh-keygen -t ed25519` in a shell. That will generate a private and a public key file, place these inside the `.ssh` folder for easy access
2. Go to your Proxmox server, and in one of the nodes open a Shell instance. There, edit the authorized SSH keys file by running `nano .ssh/authorized_keys` and adding the contents of `[your-ssh-key-name].pub` on a new line. Save the file and exit
3. Validate the connection by opening a terminal on the host computer, and running `ssh root@[your-proxmox-server-ip]`

## Installing Ansible
1. Install [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-on-specific-operating-systems)
2. Verify your installation by running `ansible --version`
3. Install Ansible-Lint
`pip install ansible-lint`
4. Install the Ansible `community.general` collection to install the Proxmox KVM module
`ansible-galaxy collection install community.general`
5. Install the Ansible `docker` collection to install the docker compose module
`ansible-galaxy collection install community.docker`
6. Install the Ansible `posix` collection to install the synchronize module
`ansible-galaxy collection install ansible.posix`
7. Install the Ansible `utils` collection to install the to_paths module
`ansible-galaxy collection install ansible.utils`
8. Install sshpass
`sudo apt install sshpass`
9. Install pass
`sudo apt install pass`
10. Create a vault file
`ansible-vault create Configuration/group_vars/all/vault`
11. Add a password for that file if asked in a popup. This will be required later if the file needs to be viewed or changed
12. Enter the following content (with your own settings) inside that file and save it
```yml
---
vault_proxmox_ssh_username: YOUR_HOMELAB_SERVER_SSH_USERNAME_FOR_SUDO_COMMANDS_ON_THE_PROXMOX_SERVER
vault_proxmox_ssh_password: YOUR_HOMELAB_SERVER_SSH_PASSWORD_FOR_SUDO_COMMANDS_ON_THE_PROXMOX_SERVER

vault_proxmox_username: YOUR_HOMELAB_SERVER_USERNAME_FOR_LOGGING_IN_TO_PROXMOX
vault_proxmox_password: YOUR_HOMELAB_SERVER_PASSWORD_FOR_LOGGING_IN_TO_PROXMOX

vault_docker_ssh_username: YOUR_DOCKER_VM_SSH_USERNAME
vault_docker_ssh_password: YOUR_DOCKER_VM_SSH_PASSWORD

vault_docker_root_password: YOUR_DOCKER_VM_ROOT_PASSWORD

vault_github_username: YOUR_GITHUB_USERNAME
vault_github_pat: YOUR_GITHUB_PERSONAL_ACCESS_TOKEN

local_repo_dir: THE_PATH_TO_THIS_REPO_IN_WSL
remote_repo_dir: THE_PATH_TO_THIS_REPO_ON_YOUR_REMOTE_SERVERS

control_node_root_password: THE_ROOT_PASSWORD_FOR_YOUR_ANSIBLE_CONTROL_NODE
```
12. Remove the placeholder `Configuration/group_vars/all/vault.example` file
13. You are now ready to run the playbooks using the `ansible-playbook` command. You will be instructed later when you should run playbooks. **If there are issues with the vault password file when trying to run the playbooks**, you could circumvent that by adding the parameter `--ask--vault-pass` to the end of the `ansible-playbook` command if you are having a hard time fixing the issue.

## Setting up the server
1. With a fresh proxmox installation, go into `Datacenter -> Resource Mappings` and add a mapping for the HBA if you have one with the name `HBA` under `PCI Devices`. Also add your Zigbee USB stick if you have one under USB Devices, with the name `Zigbee`. If you do not have an HBA, you need to comment out that line in the file `Configuration/group_vars/homelab_proxmox/vars.yml`
2. If you want to store the Docker VM on another disk mirror, create a ZFS-mirror through `Datacenter -> farm -> Disks -> ZFS -> Create: ZFS` with the name `dockerpool` and the RAID Level `Mirror`
3. Enter your homelab name in the file `Configuration/group_vars/homelab_proxmox/vars.yml`, by replacing the `api_host` and `node` values. Also check that the `local_storage_name` is set to match your setup. Set the `docker_storage_name` equal to `local_storage_name` if you want to store the Docker VM on the same pool, or choose another name if you want to place it there, for example `dockerpool` if you created that in the previous step. The `api_host` and `node` values are required because the deployment script needs to find the correct Proxmox instance, which is does by name
4. Run the proxmox pre-setup playbook
`ansible-playbook setup/pre-proxmox-setup.yml`
5. Go into the `Configuration/group_vars/homelab_proxmox/vars.yml` file and change the `enabled` attribute to `false` for the modules you do not want
6. Run the proxmox setup playbook
`ansible-playbook setup/proxmox-setup.yml`
7. Start the VMs, and enter their IPs into the `Configuration/hosts.yml file`

## Setting up the Docker VM
1. Complete the debian setup through the GUI by selecting the VM in proxmox, and selecting Console. Use the settings below, if you want to can follow along with [this guide](https://www.youtube.com/watch?v=gGsgl0t8py0)
  - Hostname: docker
  - Domain name: docker.local
  - Full name for the new user: docker
  - Username for your account: docker
  - Partitioning method: Guided - use entire disk and set up LVM
  - Disk to partition: SCSI1 (sda)
  - Partitioning scheme: All files in one partition
  - Write the changes to disks and configure LVM: Yes
  - Amount of volume group to use for guided partitioning: max
  - Write the changes to disks: Yes
  - Scan extra installation media: No
  - Debian archive mirror: deb.debian.org
  - HTTP proxy information: (blank)
  - Participate in the package usage survey: No
  - Software to install: SSH server, standard system utilities
2. Create a vault file for the docker setup by running `ansible-vault create Configuration/group_vars/homelab_docker/vault` and enter the following (modifying the values according to your needs):
```yml
---
configuration_repository_name: YOUR_CONFIGURATION_REPOSITORY_NAME

docker_container_repositories:
  - Repository 1 name
  - Repository 2 name
  - ...

docker_static_website_repositories:
  - Repository 1 name
  - Repository 2 name
  - ...

docker_nfs_mounts:
  - { src: '/some/nfs/mount', path: '/mnt/local/mount/path', opts: 'rw' }
  - { src: '/some/readonly/nfs/mount', path: '/mnt/readonly/mount', opts: 'ro' }
```
Here, `docker_container_repositories` are all the repositories your docker containers will require, **except** static website repositories (they will be hosted with PHP, so they can either be static HTML or PHP projects). Those should be placed in `docker_static_website_repositories` instead. The docker setup script will clone all these repositories for you, that you may then reference in docker composes or playbooks
3. Remove the placeholder `Configuration/group_vars/homelab_docker/vault.example` file
4. Run the `setup/docker_setup.yml` playbook (note that you might have to manually SSH into the VM from the Ansible controller first to set the keys up, so Ansible can connect)
5. Inside the project folders of the `Configuration/docker/` folder, create `.env.ENV_NAME_HERE.vault` files using `ansible-vault create Configuration/docker/PROJECT_NAME_HERE/.env.ENV_NAME_HERE.vault`, and enter the environment variables needed by the project in there. For example for the dev environment of the backend for the `FullStackWebApp` example, you would run `ansible-vault create Configuration/docker/FullStackWebApp/Backend/.env.dev.vault`
6. Go to the Portainer instance at `https://DOCKER_VM_IP_HERE:9443` and create a password for the `admin` user
7. Run the different deployment scripts for the projects, following the syntax `ansible-playbook deploy/STACK_NAME_HERE-deploy.yml --extra-vars env=ENV_NAME_HERE` where `ENV_NAME_HERE` is either `dev` or `prod`

### Setting up Cloudflare DDNS
If you do not want to set up Cloudflare DDNS, you can skip this part.
1. Copy the file located in `ConfigurationExample/Containers/Cloudflare_DDNS/config.example.json` and rename it, so it is located at `/Homelab/Configuration/Containers/Cloudflare_DDNS/config.json` on the docker VM
2. Replace the api token with one you generate, through `Cloudflare Dashboard -> My Profile -> API Tokens -> Create Token -> Edit zone DNS template, choose the correct zone from the dropdown and save`

### Connecting to a Database
Once Portainer is up and running, you should be able to connect to the SQL Server database. You can try that it works by SSHing into the portainer VM, then running `docker exec -it sqlserver "bash"` to start an interactive bash terminal inside the `sqlserver` docker container, then running `/opt/mssql-tools/bin/sqlcmd -S localhost -U SA`, entering the SA account password (from the `.env.dev.vault` file). It should then display `1>` if it is working, according to the [documentation](https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker?view=sql-server-ver16&preserve-view=true&pivots=cs1-bash#connect-to-sql-server).

If that works, you should also be able to remote into the SQL server instance as long as you have network access to the server, for example by using a computer on the same network. Through SSMS, you can connect to the instance by selecting `Database Engine` as the server type, entering `tcp:IP_OF_PORTAINER_VM_HERE,1433`, substituting with the correct IP, choosing `SQL Server Authentication` with `SA` as the Login and the password from the `.env.dev.vault` file.

## Debugging Docker container deployments
If you are having issues when trying to set up a new docker container deployment, you can follow the below steps to hopefully gain more insight into the issue.
1. Go to the folder where the project with the Dockerfile is stored
2. Add a `RUN ls` to the Dockerfile where you would like to debug the files. To list files inside a folder, you can use the command `RUN ls folder_name`
3. Run `docker build --progress=plain --no-cache .` to build the container and see the output
4. You can also use the VS Code Docker extension to see the file system inside the containers etc

## Setting up Home Assistant
If you do not want a Home Assistant VM, you can skip this part.
### Creating the VM
The VM is created using *ttecks* helper script. You can find it on [his website](https://tteck.github.io/Proxmox/) under `Home Assistant -> Home Assistant OS VM`, but here is the command: 

```bash
bash -c "$(wget -qLO - https://github.com/tteck/Proxmox/raw/main/vm/haos-vm.sh)"
```

Run this in the Proxmox console, `Datacenter -> homelabservername -> Shell`.
I have allocated 32GB of disk space and 8GB of RAM to the VM, in the installer you have the possibility to customize your installation if you want.

### Adding Zigbee USB device
If you do not have a Zigbee USB stick, you can skip this part.
1. On the VM, under `Hardware`, select `Add -> USB Device -> Use mapped Device -> Zigbee`. I couldn't find a way to automate this through Ansible, as I was able to with the mapped PCI device

### Setting up Zigbee2MQTT
If you do not have a Zigbee USB stick or do not want to use Zigbee2MQTT, you can skip this part.
Reference: https://www.youtube.com/watch?v=4y_dDgo0i2g but with changes
1. `Settings -> Add-ons -> Add-on store -> Mosquitto broker -> Install`
2. Go to the Mosquitto broker add-on, under Info enable `Start on boot` and `Watchdog`. Finally, start the add-on
3. `Settings -> Devices & services -> mqtt popup -> Configure -> Submit -> Finish`
4. `Settings -> Add-ons -> Add-on store -> top right three dots -> Repositories` and enter `https://github.com/zigbee2mqtt/hassio-zigbee2mqtt` then Add and Close, then refresh browser
5. Select the `Zigbee2MQTT` add-on, install and enable `Watchdog`, `Show in sidebar` and `Start on boot`
6. Under Configuration, in the `serial` field, enter the following:
```
port: USB_PORT_HERE
adapter: ezsp
```
replacing with the path to the Zigbee USB stick, with you can find under `Settings -> System -> Hardware -> All hardware -> Search for USB, and expand the correct one, then you have it under ID`
IMPORTANT NOTE: The `adapter` part is only needed for some Zigbee sticks, for example the Sonoff ZBDongle-E (SONOFF-ZB-USB-E) needs to have it, but it should be omitted for other sticks, like the Sonoff USB ZigBee dongle (SONOFF-ZB-USB). Check the settings depending on which stick you have
7. Under `Info`, click Start
8. To add devices, press the button in the top to allow all connections, then put the device into pairing mode

### Setting up Tailscale for remote access
1. Add the Tailscale add-on and set it up
2. Use the Tailscale IP of the Home Assistant VM as the external URL, for example `http://100.100.100:8123`

### Setting up Node-RED
1. `Settings -> Add-ons -> Add-on store -> Node-RED -> Install`
2. Go to the Node-RED add-on, under Configuration enter a password and disable SSL, then select Save. Then, under Info, enable `Start on boot` and `Watchdog`. Finally, start the add-on

### Installing HACS
Reference: https://www.wundertech.net/how-to-install-hacs-on-home-assistant/
Summary:
1. Install the `Terminal & SSH` add-on
2. Run the following command: `wget -O - https://get.hacs.xyz | bash -`
3. Restart Home Assistant with `ha ha restart`
4. Add the `HACS` integration
5. Follow the installation guide
6. Restart Home Assistant through `Settings -> System -> Hardware -> Restart Home Assistant`

### Setting up Gmail notifications
1. Follow [this guide](https://www.home-assistant.io/integrations/google_mail/) to set up the Gmail integration
2. To test that it works, go to `Developer tools -> Services -> Select the service here, it should start with Notifications and contain your email address with underscores`
3. Enter a `message` and optionally a `title`. Under `target`, enter the email address you want to send an email to
4. Press `Call service` and check that the email went through

### Setting up low battery warnings
1. Import the blueprint from [here](https://community.home-assistant.io/t/low-battery-level-detection-notification-for-all-battery-sensors/258664)
2. Under `Actions`, choose `Call service` and select the email notification service. It should start with `Notifications:` and contain your email address with underscores
3. Edit the code in YAML and change it to this (but keep the service part, instead of this placeholder), and change the targets
```yaml
service: notify.your_email_with_underscores
data:
  title: "[HA] Low Battery"
  message: "<h1>Low battery warning!</h1><br><b>Sensors:</b><br>{{sensors}}"
  target:
    - first.target@email.com
    - second.target@email.com
```

### Setting up custom binary sensors
1. Install the `File editor` add-on
2. Enable `Start on boot`, `Watchdog`, `Auto update` and `Show in sidebar`
3. Start the add-on
4. Open the file editor, and in the `/config` folder, locate `configuration.yaml`
5. Add the following line to it:
```
binary_sensor: !include binary_sensor.yaml
```
6. Create a new file, name it `binary_sensor.yaml`
7. Add your custom sensors in that file, for example an on/off state depending on whether something is drawing power:
```yaml
- platform: template
  sensors:
    homelab_status:
      friendly_name: "Homelab Running"
      value_template: "{{ states('sensor.outlet_power_sensor_name')|float > 2.0 }}"
```

### Fixing Shelly device push update failure
Reference: https://www.home-assistant.io/integrations/shelly/#shelly-device-configuration-generation-1
1. If you are using a Wifi network with several access points, enable `Client AP Roaming` under `Internet & Security`
2. Under `Internet & Security`, under `ADVANCED - DEVELOPER SETTINGS`, enable `CoIoT` and in the `CoIoT peer` field, enter `HOME_ASSISTANT_IP_HERE:5683`, replacing with your home assistant IP but keeping the port
3. Restart the device, through `Settings -> DEVICE REBOOT`

## Setting up TrueNAS Scale
Configure your instance as you need and create the shares you need.
### Accessing TrueNAS Scale SMB shares from the Ansible controller
1. Create a vault file
`ansible-vault create Configuration/group_vars/controller/vault`
2. Add a password for that file if asked in a popup. This will be required later if the file needs to be viewed or changed
3. Enter the following content (with your own settings) inside that file and save it
```yml
---
controller_smb_mounts:
  - { src: '//TRUENAS_SCALE_IP_HERE/TRUENAS_SCALE_MOUNT_PATH_HERE', path: 'CONTROLLER_MOUNT_PATH_HERE', opts: 'username=SMB_USERNAME_HERE,password=SMB_USERNAME_HERE,vers=3' }
```
4. Remove the placeholder `Configuration/group_vars/controller/vault.example` file
5. Run the controller setup with `ansible-playbook setup/controller-setup.yml`

### Installing Emby
1. Under `Datasets`, create a new dataset named `configs`
2. Select the `configs` dataset, and add a new dataset named `emby-config` so that it becomes the child of `configs`
3. Under `Apps` -> `Available Applications`, install Emby with the following settings:
  
  Application Name: emby
  
  Environment Variables for Emby Server:
    Note: Double check that these match with the `emby` user under `Credentials` -> `Local Users`, and that the user/group has the right permissions on the datasets you need
    - UID: `1000`
    - GID: `100`
    - GIDLIST: `100`
  
  Enable Host Network: yes
  
  Enable Host Path for Emby Server Config Volume: yes
  
  Host Path for Emby Server Config Volume: choose the `emby-config` dataset you created
  
  Emby Server Extra Host Path Volumes: add your libraries here, for example if you have images on `/mnt/homelab-storage/images` you would select that as `Host Path`, and under `Mount Path in Pod` you would enter `/storage/images` if you want it named `images`

## Setting up proxbox (a copy of the server for development and testing purposes)
This is useful for development of this project, as it allows you to virtualize a new homelab server, treating it as a new homelab. In that nested server running Proxmox, you can run the playbooks to validate that everything works, and easily wipe the VM to start over from scratch, making sure you have not forgotten to automate or document any required steps.

1. Check that your CPU supports nested virtualization
  For AMD CPUs, run
  `cat /sys/module/kvm_amd/parameters/nested`
  For Intel CPUs, run
  `cat /sys/module/kvm_intel/parameters/nested`.
  If the output is `Y` or `1`, nested virtualization is supported. If it is `N` or `0`, it is not.
  Check out [how to enable it](https://ostechnix.com/enable-nested-virtualization-in-proxmox/) if it is disabled.
  Since we will run Proxmox inside Proxmox, nested virtualization is required for creating the proxbox development environment

2. Create a new VM in Proxmox, setting `CPU type` to `host` and assigning it the Proxmox ISO
3. Start the VM, complete the Proxmox installation
4. Enable ssh access by running `nano .ssh/authorized_keys` and adding the same SSH key as you used for the main server on a new line
5. Connect to the proxbox instance by running `ssh root@PROXBOX_IP_HERE` and check that it works
6. Go into the Homelab Proxmox UI (not the proxbox UI) and stop the VM, right click it and select Convert to template
7. Rename the template to `proxbox-template`
8. Right click the template, select `Clone`, give it a name and start the cloned container
9. Edit the `Configuration/group_vars/homelab_proxmox/vars.yml` file, changing the settings as you wish. For the best setup, you should use the same configuration as for the homelab server itself, but you could decrease the resources such as RAM or disk space as this is only for testing. However, be careful with decreasing the disk space too much, you could run into issues where you run out of disk space, meaning you would have to recreate the VM to increase the disk space
10. Now you can run the Ansible scripts for setting up the server, as long as you change `ansible.cfg` to use the `dev-hosts.yml` inventory file instead of `hosts.yml`. Before running Ansible scripts on the containers, you also need to manually SSH into them first to set up the fingerprints

## Deployment
Run the correct deployment scripts, depending on what you want to deploy. Adding tags means Ansible will skip any tasks without those specific tags, which allows you to deploy only a specific project.
An example could be
`ansible-playbook Configuration/deploy/web-deploy.yml --tags homer --extra-vars env=dev`
or, to deploy all `infra` projects to PROD,
`ansible-playbook Configuration/deploy/infra-deploy.yml --extra-vars env=prod`

Note that if using the `deploy-docker` or `deploy-static-web` roles to deploy, you can even use templating inside the docker compose files.

## Creating database backups
1. Connect to the database through SSMS, then right click the database and select `Tasks -> Back Up...`
2. As the source, select the correct database, and for `Backup type` select Full
3. Under destination, for `Back up to:`, select `Disk`, and then enter `/var/opt/mssql/data/DatabaseBackup`
4. Open a new WSL instance, and enter `scp root@DOCKER_IP_HERE:/Deploy/DATABASE_PROJECT_PATH_HERE/data/DatabaseBackup ./Database-DATE_HERE.bak`
5. Execute `explorer.exe .` to open an Explorer window in that folder, taking you directly to the backup file which you can then move to where you would like to store it

# Thanks
Special thanks to [Jeff Geerling](https://github.com/geerlingguy) for the Ansible roles that were really helpful to this project.