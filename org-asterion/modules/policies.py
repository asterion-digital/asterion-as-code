#####################################################################################
# Manage asterion aws policies for this stack
#####################################################################################
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions

# Define and attach an asterion assumerole policy for this stack
def create_attach_assumerole_policy(resources, groupname):

    # Create a policy document for the `admins` group providing permissions over master account global resources
    assumerole_policy_document = aws.iam.get_policy_document(
        statements=[

            # Create the assumerole policies
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "sts:AssumeRole"
                ],
                effect="Allow",
                resources=resources
            ),

            # Create the aws billing policies
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "aws-portal:ViewBilling",
                    "aws-portal:ViewUsage",
                    "aws-portal:ViewAccount",
                    "aws-portal:ViewBudget",
                    "ce:GetPreferences",
                    "ce:DescribeReport",
                    "ce:ListTagsForResource"
                ],
                effect="Allow",
                resources=["*"]
            ),

            # Create the read-only iam policies
            aws.iam.GetPolicyDocumentStatementArgs(
                actions=[
                    "iam:Get*",
                    "iam:List*",
                    "iam:Generate*",
                    "organizations:List*"
                ],
                effect="Allow",
                resources=["*"]
            )
        ]
    )

    # Create a policy from the policy document
    assumerole_policy = aws.iam.Policy(
        "asterion-group-admins-assumerole-policy",
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

    # # Create a policy document to control read-only billing permissions
    # readbilling_policy_document = aws.iam.get_policy_document(
    #     statements=[
    #         aws.iam.GetPolicyDocumentStatementArgs(
    #             actions=[
    #                 "aws-portal:ViewBilling",
    #                 "aws-portal:ViewUsage",
    #                 "aws-portal:ViewAccount",
    #                 "aws-portal:ViewBudget",
    #                 "ce:GetPreferences",
    #                 "ce:DescribeReport",
    #                 "ce:ListTagsForResource",
    #                 "ce:ListTagsForResource",
    #             ],
    #             effect="Allow"
    #         )
    #     ]
    # )

    # # Create a policy from the policy document
    # readbilling_policy = aws.iam.Policy(
    #     "asterion-group-admins-readbilling-policy",
    #     description="Read-only billing policy for the asterion-admins group",
    #     policy=readbilling_policy_document.json
    # )

    # # Attach the readbilling policy document to the admins group policy
    # readbilling_policy_attach = aws.iam.GroupPolicyAttachment(
    #     "asterion-group-admins-policy-attachment",
    #     group=groupname,
    #     policy_arn=assumerole_policy.arn,
    #     opts=pulumi.ResourceOptions(
    #         depends_on=[assumerole_policy]
    #     )
    # )

# TODO: Define and attach asterion resource policies for admin users in this stack -- 

# Allow users to modify THEIR OWN iam re accesskeys -- TEST AND CHECK

# TODO: Allow admin users to be able to deploy all services in dev aws account