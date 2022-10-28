"""A pulumi program to deploy wordpress to kubernetes via helm on the asterion infra."""

import pulumi
import random
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs,PodSpecArgs, PodTemplateSpecArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs, Chart, LocalChartOpts
from pulumi_kubernetes.helm.v3.helm import ChartOpts
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

# Get pulumi config
config = pulumi.Config()

# Get stack reference org
stackRefInfraOrg = config.require("stackRefInfraOrg")

# Set stack reference project
stackRefInfraProject = config.require("stackRefInfraProject")

# Get stack reference environment based upon app environment
stackRefInfra = pulumi.get_stack()

# Get infra stack
rpiStackRef = pulumi.StackReference(f"{stackRefInfraOrg}/{stackRefInfraProject}/{stackRefInfra}")

# Get kubeconfig path
kube_path = rpiStackRef.get_output("kube_path")

# Deploy mariadb helm chart pod
mariadb = Chart(
    "wpdev-mariadb",
    LocalChartOpts(
        path="./charts/mariadb"
    )
)

# Deploy wordpress helm chart pod
wordpress = Chart(
    "wpdev-wordpress",
    LocalChartOpts(
        path="./charts/wordpress"
    )
)

# Export values to output
pulumi.export('Kube path from RPI Infra stack', rpiStackRef.get_output("kube_path"))