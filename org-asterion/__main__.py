"""A pulumi program to deploy asterion-digital oganization to aws."""

import pulumi
import pulumi_aws as aws
import json
import datetime
from pulumi import Config, ResourceOptions, export, Output

# Blueprint for creating an aws asterion-org object
class org:

    # Default constructor
    def __init__(self, name):
        self.name = name
        self.org = object
        self.rootid = object

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
        self.rootid = self.org.roots[0].id

    # Check if an aws organization exists for this account
    def org_exists(self):
        try:
            self.org = aws.organizations.get_organisation()
            self.rootid = self.org.roots[0].id
            if self.org.roots[0] is None:
                return False
            else:
                return True
        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'org_exists()' method of the 'org' class")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))
            return False

# Obtain pulumi configuration file contents
config = Config()

# Obtain dev stack iam username from pulumi config file
new_username = config.require('newUsername')

# Create an aws object for the asterion-infra-aws organization
asterion_infra_aws_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_infra_aws_org.org_exists():
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

# Create an asterion group for the users
admin_group = aws.iam.Group(
    "admins",
    path="/users/"
    )

# Create asterion infra-aws iam users
new_user = aws.iam.User(
    'new-user',
    name=new_username,
    force_destroy=True
    )

# Create a login profile for the users
new_user_login = aws.iam.UserLoginProfile(
    "asterion-user-login-profile-new_user",
    user=new_user.name
)

# Obtain an aws access key and apply to the new user
new_user_access_key = aws.iam.AccessKey(
    "asterion-infra-aws-user-access-key",
    user=new_user.name
)

# Export password for the user
export("New user password", new_user_login.password)

# Export access key for the user
export("Encrypted secret access key", new_user_access_key.encrypted_secret)
export("Secret access key", new_user_access_key.secret)

# Add the users to the admin group
admin_team = aws.iam.GroupMembership(
    "asterion-admin-team",
    users=[
        new_user.name
    ],
    group=admin_group.name
)

# Create asterion infra-aws environment accounts
asterion_infra_aws_dev_acc = aws.organizations.Account(
    "asterion-infra-aws-dev-team",
    email="asterion-dev-team@asterion.digital",
    name="Asterion Infra-AWS Dev Team",
    parent_id=asterion_infra_aws_dev.id,
)
asterion_infra_aws_test_acc = aws.organizations.Account(
    "asterion-infra-aws-test-team",
    email="asterion-test-team@asterion.digital",
    name="Asterion Infra-AWS Test Team",
    parent_id=asterion_infra_aws_test.id
)
asterion_infra_aws_prod_acc = aws.organizations.Account(
    "asterion-infra-aws-prod-team",
    email="asterion-prod-team@asterion.digital",
    name="Asterion Infra-AWS Prod Team",
    parent_id=asterion_infra_aws_prod.id
)

# Create a role
admin_role = aws.iam.Role(
    "asterion-infra-aws-admin-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Sid": "",
            "Principal": {
                "Service": "ec2.amazonaws.com",
            },
        }],
    }))