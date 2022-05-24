"""An AWS Python Pulumi program to manage setup of the org-asterion-dev aws account"""

import pulumi
import pulumi_aws as aws
import json
from pulumi import Config, Output

# Obtain the pulumi configuration
config = Config()

# Ensure we obtain the stacks from the proper environment (E.G 'dev', 'prod' etc)
stack = pulumi.get_stack()

# Obtain the pulumi account 'organization' field from the config
org = config.require("currentOrg")

# Obtain the `org-asterion` pulumi stack
org_asterion_stack = pulumi.StackReference(f"{org}/org-asterion/{stack}")

# Obtain `org-asterion` output objects
root_account_id = org_asterion_stack.get_output("Asterion aws org account id")
dev_account_id = org_asterion_stack.get_output("Dev Account ID")

# Export the dev aws account id from the `org-asterion` stack
pulumi.export("org-asterion AWS Account ID", root_account_id)
pulumi.export("org-asterion-dev AWS Account ID", dev_account_id)