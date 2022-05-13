"""A pulumi program to deploy asterion-digital oganization to aws."""

import pulumi
import pulumi_aws as aws
import json
from pulumi import Config, ResourceOptions, export

# Blueprint for creating an aws asterion-org object
class org:

    # Default constructor
    def __init__(self, name):
        self.name = name
        self.org = aws.organizations.get_organization()
        self.rootid = self.org.roots[0].id

    # Static method to create an aws organization
    def create_org(self):
        
        # Create an aws organization for this current account
        self.org = aws.organizations.Organization(
            self.name,
            aws_service_access_principals=[
                "cloudtrail.amazonaws.com",
                "config.amazonaws.com",
                "account.amazonaws.com",
            ],
            feature_set="ALL")
        
        # Set the root id for the aws organization
        self.rootid = org.roots[0].id

    # Check if an aws organization exists for this account
    def org_exists(self):
        if self.org.id == "" or self.org.id is none:
            return False
        else:
            return True

# Obtain pulumi configuration file contents
config = Config()

# Obtain dev stack iam username from pulumi config file
new_username = config.require('newUsername')

# Create an aws object for the asterion-infra-aws organization
asterion_infra_aws_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_infra_aws_org.org_exists:
    asterion_infra_aws_org.create_org()
pulumi.export("Asterion aws org id", asterion_infra_aws_org.org.id)
pulumi.export("Asterion aws org root id", asterion_infra_aws_org.rootid)

# Create asterion infra-aws organizational unit
asterion_infra_aws = aws.organizations.OrganizationalUnit("asterion-infra-aws", parent_id=asterion_infra_aws_org.rootid)

# Create asterion infra-aws environment ou's
asterion_infra_aws_dev = aws.organizations.OrganizationalUnit("asterion-infra-aws-dev", parent_id=asterion_infra_aws.id)
asterion_infra_aws_test = aws.organizations.OrganizationalUnit("asterion-infra-aws-test", parent_id=asterion_infra_aws.id)
asterion_infra_aws_prod = aws.organizations.OrganizationalUnit("asterion-infra-aws-prod", parent_id=asterion_infra_aws.id)

# Output asterion environment ou id's
pulumi.export("asterion-infra-aws ou id", asterion_infra_aws.id)
pulumi.export("Dev ou id", asterion_infra_aws_dev.id)
pulumi.export("Test ou id", asterion_infra_aws_test.id)
pulumi.export("Prod ou id", asterion_infra_aws_prod.id)

# Create asterion infra-aws accounts
asterion_infra_aws_acc = aws.organizations.Account(
    "asterion-infra-aws-team", 
    email="2iwavQSRFqhLQ4MoTv4j44f7@asterion.digital", 
    name="Asterion Infra-AWS Full Team", 
    parent_id=asterion_infra_aws.id
)
asterion_infra_aws_dev_acc = aws.organizations.Account(
    "asterion-infra-aws-dev-team", 
    email="czmmaetwpdsmbh9pcrgtfdbe@asterion.digital", 
    name="Asterion Infra-AWS Dev Team", 
    parent_id=asterion_infra_aws_dev.id
)
asterion_infra_aws_prod_acc = aws.organizations.Account(
    "asterion-infra-aws-prod-team", 
    email="sJLPmDyY3GSYNaBrtoTwUo23@asterion.digital", 
    name="Asterion Infra-AWS Prod Team", 
    parent_id=asterion_infra_aws_prod.id
)

# Create a list containing member account id's
child_account_ids = [asterion_infra_aws.id, asterion_infra_aws_dev.id, asterion_infra_aws_prod.id]

# Initialize a list to contain policy statements allowing sub-account roles to be assumed from the management account
admin_allow_assume_policy_statements = []

# Create a list of `assumerole` policy statements covering each asterion sub-account
for child_id in child_account_ids:
    admin_allow_assume_policy_statements.append(
        json.dumps(
            {
                "Effect": "Allow",
                "Action": ["sts:AssumeRole"],
                "Resource": "arn:aws:iam::" + child_id + ":role/Administrator"
            }
        )
    )

# Create asterion infra-aws iam users
new_user = aws.iam.User(
    'new-user', 
    name=new_username
)

# Create an aws access key and apply to users
new_user_access_key = aws.iam.AccessKey(
    'new-user-access-key',
    user=new_user.name,
    opts=ResourceOptions(additional_secret_outputs=["secret"])
)

# Create a role to administer ec2 instances
# admin_role = aws.iam.Role('asterion-admin-role',
#     description='Allow administration of asterion sub-accounts',
#     assume_role_policy=new_user.arn.apply(lambda arn:
#         assume_role_policy_for_principal({'AWS': arn})
#     )
# )
admin_role = aws.iam.Role('asterion-admin-role',
    description='Allow administration of asterion sub-accounts'
)

# Create a role policy using the policy statements list
admin_assume_role_policy = aws.iam.Policy(
    'asterion-assume-admin-role-policy',
    description="Policies to allow admin role assumption in all asterion environments",
    policy=json.dumps({
        "Version":"2012-10-17",
        "Statement": admin_allow_assume_policy_statements
    })
)

# Create an allow policy and apply to the role
# admin_role_policy = aws.iam.RolePolicy('asterion-admin-role-policy', 
#     role=admin_role,
#     policy=json.dumps({
#         'Version': '2012-10-17',
#         'Statement': [{
#             'Sid': 'AllowEC2Admin',
#             'Effect': 'Allow',
#             'Resource': '*',
#             'Action': 'ec2:*',
#         }],
#     }),
#     opts=ResourceOptions(parent=admin_role)
# )

# Export the role identifier and access keys to the environment
export('roleArn', root_admin_role.arn)
export('accessKeyId', new_user_access_key.id)
export('secretAccessKey', new_user_access_key.secret)