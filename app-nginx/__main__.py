"""A pulumi program to deploy wordpress to kubernetes via helm on the asterion rpi server."""

import pulumi
import random
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs,PodSpecArgs, PodTemplateSpecArgs
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs, Chart, LocalChartOpts
from pulumi_kubernetes.helm.v3.helm import ChartOpts
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

# Get pulumi config
config = pulumi.Config()

# Get infra stack
rpiStack = pulumi.StackReference(config.require("rpiInfraStack"))

# Get kubeconfig path
kube_path = rpiStack.get_output("kube_path")

# Deploy nginx helm chart pod
nginx = Chart(
    "asterion-infra-rpi-" + pulumi.get_stack(),
    LocalChartOpts(
        path="./charts/ingress-nginx"
    )
)