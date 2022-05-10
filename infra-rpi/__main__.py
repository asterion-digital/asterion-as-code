"""A Python Pulumi program"""
# 
# This code will setup kubernetes infrastructure on a Raspberry Pi with Ubuntu 21.10 installed.
#

import pulumi
import pulumi_command as command
from pulumi import Output

# Get pulumi config
config = pulumi.Config()

# Get settings from pulumi config
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
server_ip_address = config.require('ip_address')
kube_path = config.require('kube_path')

# Define a provider connection to the remote asterion server
connection = command.remote.ConnectionArgs(
    host=server_ip_address, 
    user='asterion',
    private_key=private_key,
    port=6833
    )

# Declare command to install k3s on the remote node
install_k3s_cmd = Output.concat(
    "curl -sfL https://get.k3s.io | sh -s - server --tls-san ", server_ip_address, " --write-kubeconfig-mode 644 --no-deploy traefik --no-deploy servicelb --data-dir /mnt/data/k3s"
    )

# Register k3s install on create and uninstall on delete with the remote node
install_k3s = command.remote.Command(
    'asterion-infra-rpi-k3s-installer',
    connection=connection,
    create=install_k3s_cmd.apply(lambda v: v),
    delete="/usr/local/bin/k3s-uninstall.sh"
)

# Output the kubeconfig on the remote node to terminal
output_kubeconfig = command.remote.Command(
    'asterion-infra-rpi-retrieve-kubeconfig',
    connection=connection,
    create="cat /etc/rancher/k3s/k3s.yaml",
    opts=pulumi.ResourceOptions(depends_on=[install_k3s])
)

# Use concat to print the pulumi stdout to a kubeconfig file in the local environment
save_kubeconfig_cmd = Output.concat(
    "echo '", output_kubeconfig.stdout, "' > ../asterion-infra-kubeconfig && sed -i 's/127.0.0.1/", server_ip_address, "/g' ../asterion-infra-kubeconfig"
    )

# Save the local kubernetes configuration file
save_local_kubeconfig = command.local.Command(
    'asterion-infra-rpi-save-local-kubeconfig',
    create=save_kubeconfig_cmd.apply(lambda v: v),
    delete="rm -rf ../asterion-infra-kubeconfig && sudo rm -rf /etc/sudoers.d/asterion-infra-sudo-profile",
    opts=pulumi.ResourceOptions(depends_on=[output_kubeconfig])
)

# Export output to the terminal window
pulumi.export('Infra server kubeconfig', output_kubeconfig.stdout)
pulumi.export('Infra server public ip', server_ip_address)
pulumi.export('github actions test', 'successful')