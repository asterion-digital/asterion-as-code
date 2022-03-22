# asterion-as-code

This readme covers setting up a Raspberry Pi (model 4b) with the necessary configurations to run Pulumi stacks over top of Kubernetes clusters.


## Preparing the raspberry pi
We'll install a USB-bootable AARCH64 (ARM) Linux Operating System (Ubuntu) into our Raspberry Pi.

### Creating an ubuntu disk image
Aside from physical hardware, you'll need to prepare a USB and SD card with an operating system image.

1. Download and install the official [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to write an OS image to the USB drive.

    > **Note:** You're not strictly limited to using the RPI Imager to perform image writing. You could use the ```dd``` command (refer [How to make disk image with dd on Linux or Unix](https://www.cyberciti.biz/faq/unix-linux-dd-create-make-disk-image-commands/)), which comes pre-built into most Linux images, performs similarly, and suits situations where you might not be able to obtain the RPI Imager.

    > **Note:** You can use snap to install the imager with `sudo snap install rpi-imager`, **however** there's RPI-specific dependencies included with this method of installation. I recommend, if using RPI Imager, to download the installer manually and install using your built-in installers. E.G: for Ubuntu, use the application _Ubuntu Software_.

2. Write a Linux image to both an SD card and a USB flash drive.

    > **Note:** For RPI 4B models older purchased during or after 2021, you should only need to write the image to a USB drive as USB boot is enabled in the RPI 4b EEPROM boot order by default.
    
    - The Raspberry Pi OS is the recommended general purpose OS built specifically for use with Raspberry Pi hardware specifications and based upon the Debain Linux distribution. However, we will use the *"Other general-purpose OS"* option to select a 64-bit Ubuntu Desktop (currently 21.10). Please note that you should use a less resource-heavy OS as Desktop distributions may have performance issues related to processing complex graphical environments.

    > **Note:** I recommend [downloading the image](https://ubuntu.com/download/raspberry-pi) first and using the *"Use custom"* option in the RPI Imager to select the downloaded image. This will significantly increase performance during image writing. If you have issues using a downloaded ISO file, please revert back to using the RPI Imager curated library to select the proper image.

    > **Note:** If using the latest version of **_Ubuntu (21.10)_**, vxlan modules were removed from this distribution into a seperate package *(linux-modules-extra-raspi)*. You'll need to install this package to ensure flannel can set up your internal cluster mesh network correctly. To install this package, use the command: ```sudo apt-get install linux-modules-extra-raspi``` before continuing with the rest of the instructions.

3. Make sure to tweak the _Advanced Options_ by clicking the cog. Ensure the following:
    - You set the _hostname_ to `asterionpi-dev`;
    - _Enable SSH_ is selected;
    - _Allow public-key authentication only_ is selected (feel free to transfer any public keys into the _authorized keys_ section - note that only one key can be accepted at present!);
    - _Set username and password_ is selected with a specific username and password;
    - _Configure wifi_ is selected with the correct SSID and password, and;
    - _Eject media when finished_ is deselected - this will enable these settings to be written to the image.
Also, ensure that the sudo/admin password you use to bypass User Access Control prompts is correct - the RPI Imager will initially work if this is wrong, but will fail when writing _config.txt_ with the advanced settings you've set above.

4. When the image has been written to the SD card/USB, put the device into the RPI and power it up!


### Configure default ubuntu boot behaviour
If this is the first time booting up your Raspberry Pi - congratulations!

You likely have an SD card in there. Now, we want to boot the RPI with Ubuntu from our bootable USB. To do this, follow these instructions, however do note that you'll only need to do this **once** as we will be updating the onboard EEPROM on the RPI. For subsequent installations on the same RPI, we should be able to just boot straight from the USB. 

Open up *Terminal* and use the following commands to configure your OS environment:
1. First, ensure all Apt packages are up-to-date (if not already).
```
sudo apt-get update
```
> **Note:** Refer section 'Ensure apt packages are up-to-date' below if you have any problems running this command.

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


## Server configuration and remote access
1. The Ubuntu bootstrapper will take you through the normal installation options and steps - be sure to make note of the username and password you've set! The installation will take several minutes to complete. 
2. Once installed, log in using the username and password supplied to the RPI Imager software above.


### Ensure apt packages are up-to-date
Run the following command to ensure that Ubuntu's apt packages are up-to-date: ```sudo apt-get update```.

If you receive the error `temporary failure resolving 'ports.ubuntu.com'` upon running the update process, ensure the following:
1. That your netplan configuration shows the correct wireless connection details.
    - Run `sudo cat /etc/netplan/50-cloud-init.yaml` and ensure the `wifis` and `ethernets` sections are correct. You can use our [50-cloud-init-example.yaml](examples/50-cloud-init-example.yaml) as a reference to what that should reasonably look like.
    > **Note:** Please ensure that the quotation marks around the SSID name in the `access-points` section is preserved!
    - Run `sudo netplan apply` or `reboot now` to allow changes to take effect.
    - Once restarted, try `sudo apt-get update` again.


### Enable the ssh service
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
> **Note:** If you have problems starting the SSH service, it's likely it hasn't been installed on the host machine: `sudo apt-get install openssh-server`


### Enable ssh key-based authentication 
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


### Secure ssh config in rpi
> **Note:** Reference [https://webdock.io/en/docs/how-guides/security-guides/ssh-security-configuration-settings](https://webdock.io/en/docs/how-guides/security-guides/ssh-security-configuration-settings) and access the SSH configuration file using `sudo nano /etc/ssh/sshd_config`

1. Open SSH config and follow the referenced link above to tweak settings.
2. Once the settings have been configured, restart the SSH service with `sudo systemctl restart sshd`


### Enable ssh remote access on a specific port at the internet gateway
1. Log in to router.
2. Open an external port <PORT NUMBER> on RPI external IP 124.248.134.230.
3. Forward to internal port 22.
4. Apply changes.


### Test connection
Connect to the host by specifying the port at which the host accepts SSH traffic.
```
ssh -p <external port number> <server username>@<server hostname/ext. ip>
```


### Monitor logs on the server for any dodgy port knocks
Use the following command to review SSH connection attempts on the network interface of our proposed server.
```
sudo cat /var/log/auth.log
```


### Enable ssh remote git access from server
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
git clone git@github.com:shawngerrard/asterion-as-code.git
```

<hr />


## Configure ubuntu local storage
By default, the RPI Imager will create a volume on the USB flash disk. If you're happy with this, you can skip this section. Otherwise, you'll need to mount any attached volumes to the operating system.

### Identify attached filesystem device
First, attach your storage if it's not already attached. Then check that your filesystem has been mounted automatically - it's quite likely that it hasn't.

```
# View the list of filesystems currently attached
df -h

# View the list of partitions for each filesystem
lsblk

# View the details of attached devices
sudo fdisk -l
```


### Format and partition attached filesystem
Before we mount the new filesystem device to our server, we must first prepare it for mounting by reformatting and partitioning as necessary.

**If your filesystem has been mounted correctly**, a _mountpoint_ will be associated with the attached filesystem (typically labelled _sda1_ or _sdb1_) in the ```lsblk``` output, and the same filesystem will be present in the `df -h` output.

**If your filesystem has *not* been mounted correctly**, we will need to perform the following commands on the RPI server:

> **Note:** You can skip the first few commands to follow which erase partitions/filesystems if you do not wish to do this.

```
# Erase the partitions on the attached volume
sudo fdisk /dev/<sda/sdb>
```

You'll see the FormatDisk menu - you'll need to interact with this to _delete_ `(d)` any volume partitions you cannot use.

You can also create a new partition in this menu with the _new_ option `(n)`.

Make this partition the _primary_ partition `(p)`.

Finally, write the partition table to the disk `(w)`.

Once this is done, exit `ctrl+c` and reboot `reboot now`.


### Mount the filesystem

```
# Format the new partition with the `ext4` fs type
sudo mkfs.ext4 /dev/sda1

# Create the directory on the volume that will be the default location of the mount point path
cd /mnt/ && sudo mkdir -p data/k3s

# Mount the volume to the mount point path set above
sudo mount /dev/sda1 /mnt/data/k3s

# Confirm the mount process succeeded
df -h
```

<hr />


## Install python 
We must install Python to be able to use this repository with Pulumi, as it uses Python to define our infrastructure as code through Pulumi.

To install Python, run:
```
sudo apt install python3-venv python3-pip
```

<hr />


## Setup local environment
If you have followed the [introductory guide](../README.org) and have Pulumi CLI installed on your local machine, it's time to configure Pulumi to operate our RPI stacks remotely from this local machine.


### Initialise an existing pulumi project
To get started with Pulumi, lets initialise our project, making sure we are in the right directory, have the python [virtual environment](https://docs.python.org/3/library/venv.html) activated, and have installed our python dependencies with [pip](https://pypi.org/project/pip/).

```
# Start from the infra directory and initialize pulumi stack
cd infra-rpi && pulumi stack init dev

# Initialize local virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install pip requirements
pip install -r requirements.txt
```


### Create configuration

Once our local environment is set up we can proceed with creating the required configuration entries in pulumi. For now this is just a local [ssh](https://www.ssh.com/academy/ssh) key.

This is the key that will be added to the infrastructure virtual machines so ensure you update the `$keyname` variable as appropriate!

Note: If you need to generate a new key you can run `ssh-keygen -t rsa -b 4096 -C <comment>`.

```
export keyname="asterion"
cat ~/.ssh/${keyname}.pub | pulumi config set publickey
cat ~/.ssh/${keyname}     | pulumi config set --secret privatekey
echo 124.248.134.230 | pulumi config set ip_address
```


### Setup default user with administrative priviledges
To be able to install K3S via Pulumi without errors, we need to provide the default Ubuntu user (*asterion*) with `sudo` privileges. 

We'll achieve this by creating a *sudo user profile* on the remote RPI. 

> **Note:** You should only need to perform this action once.

```
# Create a sudo profile for the `asterion` user on the remote machine
sudo touch /etc/sudoers.d/asterion-sudo-profile && echo "asterion ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers.d/asterion-sudo-profile
```


### Create stack and retrieve kubeconfig

Once we have our local pulumi configuration set we can bring up the infrastructure stack. Currently, this stack includes the deployment of [K3S](https://k3s.io/k3s) on an existing RPI.

```
pulumi up --yes
```

With our stack now running, lets retrieve the [k3s kubeconfig](https://rancher.com/docs/rke/latest/en/kubeconfig/) file and set this up in our local `infra-rpi` directory so that we can interact with the infrastructure later on to deploy applications.

```
# Ensure kube file exists
mkdir ~/.kube

# Output kubeconfig to file
pulumi stack output "Infra server kubeconfig" > asterion-infra-kubeconfig

# Sed replace the kubeconfig ip
ip=$(pulumi stack output "Infra server public ip")
sed -i "s/127.0.0.1/${ip}/g" asterion-infra-kubeconfig
```

<hr />