import json
import pulumi
import pulumi_aws as aws
from pulumi import Config, ResourceOptions, Output

# Create a class to update the current stack account using the default role
class UpdateStackAccount:
    
    # Define default constructor
    def __init__(self, users):

        # Define object attributes
        self.assume_role_policy = object
        self.master_account_id = Config().require("masterAccountId")
        self.pass_role_policy = object
        self.provider = object
        self.region = Config("aws").require("region")
        self.resource_policy = object
        self.role = object
        self.stack_account_id = Config().require("accountId")
        self.stack_environment = Config().require("environment")
        self.users = users

    # Static method to assume a provider role and update the stack account with admin roles and permissions
    def update_stack_account(self):

        # Create a provider that will assume the default `OrganizationAccountAccessRole` role in the asterion aws stack account
        self.provider = aws.Provider(
            "asterion-" + self.stack_environment + "-account-provider",
            assume_role=aws.ProviderAssumeRoleArgs(
                role_arn=Output.concat("arn:aws:iam::", self.stack_account_id,":role/OrganizationAccountAccessRole"),
                session_name="PulumiSession",
                external_id="PulumiApplication"
            ),
            region=self.region
        )

        # Define an inline policy document in the asterion stack account for resource permissions
        self.resource_policy = aws.iam.get_policy_document(
            statements=[

                # Allow open permissions across common aws services and logging
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "cloudwatch:*",
                        "ec2:*",
                        "elasticloadbalancing:*",
                        "lambda:*",
                        "logs:*"
                    ],
                    effect="Allow",
                    resources=[
                        "*"
                    ]
                ),
                # Grant read-only iam privileges
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "access-analyzer:List*",
                        "iam:Get*",
                        "iam:List*",
                        "iam:Generate*",
                        "iam:Simulate*"
                    ],
                    effect="Allow",
                    resources=[
                        "*"
                    ]
                )
            ],
            opts=pulumi.InvokeOptions(
                provider=self.provider
            )
        )

        # Define a policy document that allows the administrator role to be assumed
        self.assume_role_policy = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "sts:AssumeRole"
                    ],
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            identifiers=self.users.arns,
                            type="AWS"
                        ),
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            identifiers=["arn:aws:iam::814941672613:user/administrator"],
                            type="AWS"
                        )
                    ]
                )
            ],
            opts=pulumi.InvokeOptions(
                provider=self.provider
            )
        )

        # Define a policy document that allows the administrator role to pass other roles to aws services
        self.pass_role_policy = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "iam:PassRole"
                    ],
                    effect="Allow",
                    # User will be able to pass roles to all resources (services, users, roles, etc)
                    # TODO: Update to allow PassRole to be applied to specific services
                    resources=["*"]
                )
            ],
            opts=pulumi.InvokeOptions(
                provider=self.provider
            )
        )
        
        # Create a new role in the asterion dev account 
        self.role = aws.iam.Role(
            "asterion-" + str(self.stack_environment) + "-admin-role",
            assume_role_policy=self.assume_role_policy.json,
            name="administrator",
            inline_policies=[
                aws.iam.RoleInlinePolicyArgs(
                    name="asterion-" + str(self.stack_environment) + "-resource-policy",
                    policy=self.resource_policy.json
                ),
                aws.iam.RoleInlinePolicyArgs(
                    name="asterion-" + str(self.stack_environment) + "-pass-role-policy",
                    policy=self.pass_role_policy.json
                )
            ],
            opts=pulumi.ResourceOptions(
                provider=self.provider
            )
        )
