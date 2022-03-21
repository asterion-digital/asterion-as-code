"""A Python Pulumi program"""

import pulumi
import pulumi_command as command
from pulumi import Output
from pulumi_kubernetes.storage.v1 import StorageClass


# Get pulumi config
config = pulumi.Config()

# Get settings from pulumi config
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
ip_address = config.require('ip_address')

###########################################################

# Define a storage class for persistent volumes on the cluster
# TO DO 1: transfer code to infra codebase
sc = StorageClass(
    "asterion-dev-sc-localfs1",
    provisioner="kubernetes.io/no-provisioner",
    volume_binding_mode="WaitForFirstConsumer"
)

# Define a persistent volume for the cluster
# TO DO 1: specify dependence on SC?
# TO DO 2: transfer code to infra codebase
pv = PersistentVolume(
    "asterion-dev-pv-localfs1",
    metadata={},
    spec={
        "access_modes": [ "ReadWriteOnce" ],
        "capacity": {
            "storage": "100Gi"
        },
        "local": {
            "path": "/mnt/data/k3s",
            "fs_type": "ext4"
        },
        "node_affinity": {
            "required": {
                "node_selector_terms": [ {
                    "match_expressions": [ {
                        "key": "kubernetes.io/hostname",
                        "operator": "In",
                        "values": [ "litrepublicpi" ]
                    } ]
                } ]
            }
        },
        "storage_class_name": "asterion-dev-sc-localfs1",
        "volume_mode": "Filesystem"
    }
)

###########################################################



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