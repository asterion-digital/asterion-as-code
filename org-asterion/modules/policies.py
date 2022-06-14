#####################################################################################
# Manage asterion aws policies for this stack
#####################################################################################
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions

# Define and attach aws policies that govern administrators of the asterion master account
def create_attach_policies(resources, groupname):

    # Create a policy document that will be converted to json
    policy_document = aws.iam.get_policy_document(
        statements=[

            # Allow administrators to switch iam roles
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "sts:AssumeRole"
                ],
                effect="Allow",
                resources=resources
            ),

            # Allow administrators to view aws billing information
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "aws-portal:View*",
                    "ce:Get*",
                    "ce:Describe*",
                    "ce:List*"
                ],
                effect="Allow",
                resources=["*"]
            ),

            # Allow administrators to view aws iam information
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "iam:CreateAccessKey",
                    "iam:Get*",
                    "iam:List*",
                    "iam:Generate*",
                    "organizations:List*"
                ],
                effect="Allow",
                resources=["*"]
            ),

            # Allow administrators to view aws ec2 information
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "ec2:Describe*",
                    "ec2:Get*",
                    "ec2:List*",
                    "ec2:View*",
                    "elasticloadbalancing:Describe*",
                    "elasticloadbalancing:Get*",
                    "elasticloadbalancing:List*",
                    "elasticloadbalancing:View*"
                ],
                effect="Allow",
                resources=["*"]
            )
        ]
    )

    # Create a policy from the policy document
    policy = aws.iam.Policy(
        "asterion-secpolicies-admins-group-policy",
        description="Policies for the asterion-admins group",
        policy=policy_document.json
    )

    # Attach the policies to the `admins` iam group
    policy_attach = aws.iam.GroupPolicyAttachment(
        "asterion-secpolicies-admins-group-policy-attachment",
        group=groupname,
        policy_arn=policy.arn,
        opts=pulumi.ResourceOptions(
            depends_on=[policy]
        )
    )

# TODO: Allow admin users to be able to deploy all services in dev aws account