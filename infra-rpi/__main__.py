"""A Python Pulumi program"""

import pulumi
from pulumi_command import Local, Remote, Types

# Get pulumi config
const config = new Config()
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
ip_address = config.require('ip_address')


# define provider connection
connection = command.remote.ConnectionArgs(host=ip_address, user='asterion',private_key=private_key)

install_cmd = Output.concat("curl -sfL https://get.k3s.io | sh -s - server --tls-san ", ip_address, " --write-kubeconfig-mode 644 --no-deploy traefik --no-deploy servicelb --data-dir /mnt/data/k3s")

install_k3s = command.remote.Command('asterion-infra-rpi-install-k3s',
    connection=connection,
    create=install_cmd.apply(lambda v: v)
)

