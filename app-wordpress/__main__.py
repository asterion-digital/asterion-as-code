"""A pulumi program to deploy asterion wordpress on kubernetes via helm."""

import pulumi
import random
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PersistentVolume, PodSpecArgs, PodTemplateSpecArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs, Chart, LocalChartOpts
from pulumi_kubernetes.helm.v3.helm import ChartOpts
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.storage.v1 import StorageClass

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

# Deploy mariadb helm chart pod
# TO DO 1: specify dependence on PV in chart?
mariadb = Chart(
    "wpdev-mariadb",
    LocalChartOpts(
        path="./charts/mariadb"
    )
)

# Deploy wordpress helm chart pod
# TO DO 1: specify dependence on PV in chart?
wordpress = Chart(
    "wpdev-wordpress",
    LocalChartOpts(
        path="./charts/wordpress"
    )
)