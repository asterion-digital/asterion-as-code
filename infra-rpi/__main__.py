"""A Python Pulumi program"""

import pulumi
import pulumi_command as command
from pulumi import Output

# Get pulumi config
config = pulumi.Config()

# Get settings from pulumi config
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
server_ip_address = config.require('ip_address')

# Define a remote provider connection to the asterion server
connection = command.remote.ConnectionArgs(
    host=server_ip_address, 
    user='asterion',
    private_key=private_key,
    port=6833
    )

# Declare command to install k3s on the remote node
install_cmd = Output.concat(
    "curl -sfL https://get.k3s.io | sh -s - server --tls-san ", ip_address, " --write-kubeconfig-mode 644 --no-deploy traefik --no-deploy servicelb --data-dir /mnt/data/k3s"
    )

# Send the k3s installation command to the remote note
install_k3s = command.remote.Command(
    'asterion-infra-rpi-install-k3s',
    connection=connection,
    create=install_cmd.apply(lambda v: v)
)

# Declare command to retrieve kubeconfig from the remote node
retrieve_kubeconfig = command.remote.Command('asterion-infra-retrieve-kubeconfig',
    connection=connection,
    create='cat /etc/rancher/k3s/k3s.yaml',
    opts=pulumi.ResourceOptions(depends_on=[install_k3s])
)

# Export output to the terminal window
pulumi.export('Infra server kubeconfig', retrieve_kubeconfig.stdout)
pulumi.export('Infra server public ip', ip_address)