#####################################################################################
# Manage asterion aws policies for this stack
#####################################################################################
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions

# Define and attach an asterion assumerole policy for this stack
def create_attach_assumerole_policy(resources, groupname):

    # Create a policy document for the assumerole policies
    assumerole_policy_document = aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "sts:AssumeRole"
                ],
                effect="Allow",
                resources=resources
            )
        ]
    )

    # Create a policy from the policy document
    assumerole_policy = aws.iam.Policy(
        "asterion-group-admins-policy",
        description="AssumeRole policy for the asterion-admins group",
        policy=assumerole_policy_document.json
    )

    # Attach the assumerole policy document to the admins group policy
    assumerole_policy_attach = aws.iam.GroupPolicyAttachment(
        "asterion-group-admins-policy-attachment",
        group=groupname,
        policy_arn=assumerole_policy.arn,
        opts=pulumi.ResourceOptions(
            depends_on=[assumerole_policy]
        )
    )

# Define and attach asterion resource policies for admin users in this stack

# Allow users to modify THEIR OWN iam re accesskeys

# Allow admin users to be able to deploy all services in dev aws account