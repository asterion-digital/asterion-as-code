"""A pulumi program to deploy asterion wordpress on kubernetes via helm."""

import pulumi
import random
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.helm.v3.helm import ChartOpts
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs, Chart, LocalChartOpts

# Generate mariadb password
#mariadb_root = random.RandomPassword("mariadb-root-password", length=12)
#mariadb_pass = random.RandomPassword("mariadb-password", length=12)

# Deploy the wordpress standalone mariadb
mariadb = Release(
    "wpdev-mariadb",
    ReleaseArgs(
        chart="mariadb",
        repository_opts=RepositoryOptsArgs(
            repo="https://charts.bitnami.com/bitnami",
        ),
        # Override chart values.
        version="10.3.7",
        values={
            "image": {
                "registry": "ghcr.io",
                "repository": "zcube/bitnami-compat/mariadb",
                "tag": "10.6"
            },
            "auth" : {
                "database": "wordpress",
                "username": "wordpress",
                "password": "wordpress"
            }
        },
    ),
)

wordpress = Chart(
    "wpdev-wordpress",
    LocalChartOpts(
        path="./charts/wordpress"
    ),
)

# Export application information
pulumi.export("Database name", mariadb.name)
