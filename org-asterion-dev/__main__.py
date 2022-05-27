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
org = config.require("currentOrgName")
account_alias = config.require("accountAlias")

# Obtain the `org-asterion` pulumi stack
org_asterion_stack = pulumi.StackReference(f"{org}/org-asterion/{stack}")

# Obtain `org-asterion` output objects
root_account_id = org_asterion_stack.get_output("asterion org account id")
dev_account_id = org_asterion_stack.get_output("asterion dev account id")
new_user_arns = org_asterion_stack.get_output("user arns")

# Export the dev aws account id from the `org-asterion` stack
pulumi.export("org-asterion aws account id", root_account_id)
pulumi.export("org-asterion-dev aws account id", dev_account_id)

# Create a provider that will assume the default `OrganizationAccountAccessRole` role in the asterion-dev account
dev_provider = aws.Provider(
    "asterion-dev-account-provider",
    assume_role=aws.ProviderAssumeRoleArgs(
        role_arn=Output.concat("arn:aws:iam::",dev_account_id,":role/OrganizationAccountAccessRole"),
        session_name="PulumiSession",
        external_id="PulumiApplication"
    ),
    region=config.require('region')
)

# Create an alias for the asterion-dev account
alias = aws.iam.AccountAlias(
    "asterion-dev-account-alias",
    account_alias=account_alias,
    opts=pulumi.ResourceOptions(
        provider=dev_provider
    )
)

# Define an inline policy document in the asterion dev account for resource permissions
asterion_dev_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=[
                "ec2:*"
            ],
            effect="Allow",
            resources=[
                Output.concat("arn:aws:ec2::",dev_account_id,":*")
            ]
        )
    ],
    opts=pulumi.InvokeOptions(
        provider=dev_provider
    )
)

# Define a policy document allowing iam `admins` group to assume a role in the asterion-dev account
assume_role_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=[
                "sts:AssumeRole"
            ],
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    identifiers=new_user_arns,
                    type="AWS"
                )
            ]
        )
    ],
    opts=pulumi.InvokeOptions(
        provider=dev_provider
    )
)

# Create a new role in the asterion-dev account 
admin_dev_role = aws.iam.Role(
    "asterion-dev-admin-role",
    name="administrator",
    assume_role_policy=assume_role_policy_document.json,
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="asterion-dev-resource-policy",
            policy=asterion_dev_policy_document.json
        )
    ],
    opts=pulumi.ResourceOptions(
        provider=dev_provider
    )
)