# asterion-as-code

This readme covers setting up a Raspberry Pi (model 4b) with the necessary configurations to run Pulumi stacks over top of Kubernetes clusters.


## Preparing the Raspberry Pi
We'll install a USB-bootable AARCH64 (ARM) Linux Operating System (Ubuntu) into our Raspberry Pi.

### Pre-requisites
Aside from physical hardware, you'll need to prepare the following:
1. Download and install the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write an OS image to the USB drive.
    > **Note:** You're not strictly limited to using the RPI Imager to perform image writing. You could use the ```dd``` command (refer [How to make disk image with dd on Linux or Unix](https://www.cyberciti.biz/faq/unix-linux-dd-create-make-disk-image-commands/)), which comes pre-built into most Linux images, performs similarly, and suits situations where you might not be able to obtain the RPI Imager.
2. Write a Linux image to both an SD card and a USB flash drive.
    > **Note:** For RPI 4B models older purchased during or after 2021, you should only need to write the image to a USB drive as USB boot is enabled in the RPI 4b EEPROM boot order by default.
    
    - The Raspberry Pi OS is the recommended general purpose OS built specifically for use with Raspberry Pi hardware specifications and based upon the Debain Linux distribution. However, we will use the *"Other general-purpose OS"* option to select a 64-bit Ubuntu Desktop (currently 21.10). Please note that you should use a less resource-heavy OS as Desktop distributions may have performance issues related to processing complex graphical environments.

    > **Note:** If using the latest version of **_Ubuntu (21.10)_**, vxlan modules were removed from this distribution into a seperate package *(linux-modules-extra-raspi)*. You'll need this package to ensure flannel can set up your internal cluster mesh network correctly. To install this package, use the command: ```sudo apt-get install linux-modules-extra-raspi``` before continuing with the rest of the instructions.

    > **Note:** I recommend [downloading the image](https://ubuntu.com/download/raspberry-pi) first and using the *"Use custom"* option in the RPI Imager to select the downloaded image. This will significantly increase performance during image writing.
3. When the image has been written to the SD card, put it into the SD reader on the RPI and power it up!

<hr />


### Ubuntu & SSH Installation and Configuration
1. The Ubuntu bootstrapper will take you through the normal installation options and steps - be sure to make note of the username and password you've set! The installation will take several minutes to complete. 
2. Once installed, log in and open your applications. Make sure to mark the *Terminal* application as a favourite, which will add it to your quick-access toolbar.

<hr />


## Ubuntu Configuration and Remote Access
We'll need to enable remote SSH access so that we can perform any maintenance remotely.

### Configure Ubuntu Boot Behaviour
Open up *Terminal* and use the following commands to configure your OS environment:
1. First, ensure all Apt packages are up-to-date.
```
sudo apt-get update
```
2. Install *net-tools* to obtain and/or verify network interface configurations.
```
sudo apt-get install net-tools
```
3. Install *raspi-config* via Apt so we can tweak the Raspberry Pi system and boot configuration.
```
sudo apt-get install raspi-config
```
4. Ensure that the EEPROM firmware is all up-to-date.
```
sudo rpi-eeprom-update
```
5. Update the RPI configuration.

    1. Open the RPI configuration manager.
    ```
    sudo raspi-config
    ```
    2. Select *Advanced Options > Boot Order* and select *USB Boot*.
    3. Commit changes and power down the RPI.
    > **Note:** It's important that the internal power-off process completes gracefully, so that the updates from the configuration manager can be applied.
    ```
    shutdown -h now
    ``` 
    4. Once the RPI has shut down, remove the SD card and insert the USB flash drive containing our Ubuntu image.

6. Once you've traversed through the initial Ubuntu configuration UI, **repeat steps 1 to 4** above.

<hr />


### Configure Ubuntu Storage Volumes
By default, the RPI Imager will create a volume on the USB flash disk. If you're happy with this, you can skip this section. Otherwise, you'll need to do some work to mount any attached volumes to the node.

First, attach your storage if it's not already attached. Then check that your filesystem has been mounted automatically - it's quite likely that it hasn't.

```
# View the list of filesystems currently mounted
df -h

# View the list of partitions for each filesystem
lsblk
```

**If your filesystem has been mounted correctly**, you should see a filesystem labelled _sda1_ or _sdb1_ in the ```df -h``` output. Check filesystem size, partitions, and the data in the mount path to verify the correct filesystem.

**If your filesystem has *not* been mounted correctly**, the filesystem has not mounted successfully, and we will need to perform the following commands on the RPI server:

> **Note:** You can skip the first few commands that erase partitions/filesystems if you do not wish to do this.

```
# Erase the partitions on the attached volume
sudo fdisk /dev/<sda/sdb>
```

You'll see the FormatDisk menu - you'll need to interact with this to _delete_ `(d)` any volume partitions you cannot use.

You can also create a new partition in this menu with the _new_ option `(n)`.

Make this partition the _primary_ partition `(p)`.

Finally, write the partition table to the disk `(w)`.

Once this is done, exit `ctrl+c` and reboot `reboot now`.

## TO DO - FINISH MOUNT INSTRUCTION

```
# Create a partition on our attached storage
# NOTE: Ensure you follow the interactive prompts that follow properly to configure the partition
sudo mkfs.ext4 /dev/sda1

# Create the directory on the volume that will be the default location of the mount path
cd /mnt/ && sudo mkdir data
```


### Enable the SSH Service
1. Check that the SSH service is running.
```
sudo systemctl status sshd
```
2. If it isn't, start the SSH service and tweak the boot order to enable USB booting.
    - Open the Raspberry Pi configuration manager.
    ```
    sudo raspi-config
    ```
    - Select *Interface Options* and enable the SSH service.
> **Note:** If you have problems starting the service, it's likely it hasn't been installed on the host machine: `sudo apt-get install openssh-server`

<hr />


### Enable SSH key-based authentication 
1. Create SSH key
    ```
    ssh-keygen -t rsa -b 4096 -C "<username>@hostname" -f ~/.ssh/<keyname>
    ```
2. Copy SSH public key to server and install into authorized_keys.
    ```
    ssh-copy-id -i ~/.ssh/<key/filename>.pub <server username>@<server hostname/ext. ip> -p <external port number>
    ```
> **Note:** Initial host key verification may fail if you've connected to this host before, and the server has a static local IP. We will need to remove the host key entry in our *known_hosts* file with `ssh-keygen -f "/path/to/known_hosts/file" -R "<RPI4 node IP address>"`. 

> **Note:** Use the following code on the host machine to remove **a single** public key from the host that may have erroneously been added:
    ```sed -i.bak '/REGEX_MATCHING_KEY/d' ~/.ssh/authorized_keys```

> **Note:** Use the following code on the host machine to remove **multiple** public keys from the host that may have erroneously been added:
    ```sed -i.bak '/REGEX1/d; /REGEX2/d' ~/.ssh/authorized_keys```

<hr />


### Secure SSH config in RPI
> **Note:** Reference [https://webdock.io/en/docs/how-guides/security-guides/ssh-security-configuration-settings](https://webdock.io/en/docs/how-guides/security-guides/ssh-security-configuration-settings) and access the SSH configuration file using `sudo nano /etc/ssh/sshd_config`

1. Open SSH config and follow the referenced link above to tweak settings.
2. Once the settings have been configured, restart the SSH service with `sudo systemctl restart sshd`

<hr />


### Enable SSH remote access on a specific port at the internet gateway.
1. Log in to router.
2. Open an external port <PORT NUMBER> on RPI external IP 124.248.134.230.
3. Forward to internal port 22.
4. Apply changes.

<hr />


### Test connection
Connect to the host by specifying the port at which the host accepts SSH traffic.
```
ssh -p <external port number> <server username>@<server hostname/ext. ip>
```

<hr />


### Monitor logs on the server for any dodgy port knocks
Use the following command to review SSH connection attempts on the network interface of our proposed server.
```
sudo cat /var/log/auth.log
```

<hr />


### Enable SSH remote Git access from server

1. Create an SSH key on the server (see above example).
2. Copy the public key contents, log in to your Github account, and enter the key data into a new PGP key entry under your Github account in _Settings/Encryption Keys/Add New Key_
```
cat ~/.ssh/<public keyname>.pub | xclip
```
3. Ensure the SSH-Agent has started and the key has been added to your agent.
```
eval `ssh-agent` && ssh-add ~/.ssh/<key/filename>
```
3. Test the connection.
```
ssh -T git@github.com
```
4. Update git config with identity values.
```
git config --global user.email "<email address>" && git config --global user.name "<user>@<hostname>"
```
5. Clone this repository.
```
git clone git@github.com:shawngerrard/pulumi-litrepublic-www-dev.git
```

<hr />


## Install Python 
We'll be using Python to define our infrastructure as code through Pulumi.

To install Python, run:
```
sudo apt install python3-venv python3-pip
```

<hr />


## Install Lightweight Kubernetes (K3S) on Server
We'll use the lightweight, server install of Kubernetes to save on resources. This will also install `kubectl` and `crictl`.

The current intention of this Raspberry Pi is to run it as a dual master/worker node. We'll be able to join in other nodes as required later.


### Install K3S
To install K3S, SSH into our proposed node and run:
```
curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode 644 --no-deploy traefik --data-dir /mnt/data/k3s/
```

### Configure K3S
We'll need to reconfigure our K3S installation so that Pulumi can manage our cluster deployments.

```
sudo mkdir -p ~/.kube && sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
export KUBECONFIG=~/.kube/config
```

<hr />


## Install Helm
We'll be using Helm as a package manager for Kubernetes. Later, we'll use Pulumi modules and Python to manipulate the process of deploying Helm Charts.


### Install Helm on Server
To install Helm on our new node, SSH into it and run the following aggregated command:
```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && chmod 700 get_helm.sh && sudo ./get_helm.sh
```

### Add a Local Helm Repo to Server
Next, we'll add a [local Helm repository](https://github.com/shawngerrard/helm-charts) to the Helm space that we've just installed, by using the following command on our node:
```
helm repo add litrepublic https://shawngerrard.github.io/helm-charts
```
> **Tip:** An advantage of using a local Helm repository is the ability to control the versioning of the Helm Charts and avoid unforeseen impacts due to any upstream updates.

<hr />


## Install and Configure Pulumi CLI on Server


### Download and install Pulumi CLI
1. Run the following command on the server to install Pulumi CLI.
```
curl -fsSL https://get.pulumi.com | sh
```

### Create a Pulumi Kubernetes provider project environment

> **Note:** If you've just cloned a Pulumi project, or wish to switch between stacks, use the following command to initialize the Pulumi stack you want. You'll then be asked for the fully-qualified name of the stack.
```
pulumi stack init
```

> **Note:** You can avoid prompts to indicate which stack you want to work on by setting the workspace to the stack
```
pulumi stack select <stack name>
```

1. Create a new Pulumi project and scaffold in the Kubernetes provider modules.
```
mkdir dev && cd dev
pulumi new kubernetes-python
```

2. Initialize a Python virtual environment to isolate project resources.
```
python3 -m venv venv
```

3. Install and update wheel so that we can install dependent Pulumi modules into our virtual environments.
```
pip3 install wheel --upgrade
```

4. Activate the virtual environment.
```
source venv/bin/activate
```

> **Tip:** Before executing the next command, ensure _requirements.txt_ is up to date with the applications/modules you want to install
5. Install project dependencies into the virtual environment.
```
pip install -r requirements.txt
```

<hr />



### Instructions for uninstalling Pulumi
From the official [Pulumi documentation](https://www.pulumi.com/docs/get-started/install/):

> To uninstall Pulumi, remove the .pulumi folder from your home directory. If you installed Pulumi manually, you should also remove the pulumi folder that was created.

<hr />


## Useful Applications 
Other applications that may be useful to install:

 - To manage source control: Git.
 ```
 sudo apt install git
 ```

<hr />