"""A Python Pulumi program"""

import pulumi
import pulumi_command as command
from pulumi import Output

# Get pulumi config
config = pulumi.Config()

# Get settings from pulumi config
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
ip_address = config.require('ip_address')

# Define a remote provider connection
connection = command.remote.ConnectionArgs(
    host=ip_address, 
    user='asterion',
    private_key=private_key,
    port=6833
    )

# Create a Python command to send to the remote node
install_cmd = Output.concat(
    "curl -sfL https://get.k3s.io | sh -s - server --tls-san ", ip_address, " --write-kubeconfig-mode 644 --no-deploy traefik --no-deploy servicelb --data-dir /mnt/data/k3s"
    )

# Trigger the K3S install command on the remote machine
install_k3s = command.remote.Command(
    'asterion-infra-rpi-install-k3s',
    connection=connection,
    create=install_cmd.apply(lambda v: v)
)