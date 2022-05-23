"""An AWS Python Pulumi program to manage setup of the org-asterion-dev aws account"""

import pulumi
import pulumi_aws as aws

# Obtain the pulumi configuration
config = pulumi.Config()

# Ensure we obtain the stacks from the proper environment (E.G 'dev', 'prod' etc)
stack = pulumi.get_stack()

# Obtain the pulumi account 'organization' field from the config
org = config.require("currentOrg")

# Obtain the `org-asterion` pulumi stack
org_asterion_stack = pulumi.StackReference(f"{org}/org-asterion/{stack}")

# Export the dev aws account id from the `org-asterion` stack
pulumi.export("org-asterion AWS Account ID", org_asterion_stack.get_output("Dev Account ID"))
pulumi.export("org-asterion-dev AWS Account ID", org_asterion_stack.get_output("Dev Account ID"))