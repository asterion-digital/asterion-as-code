"""A pulumi program to deploy asterion-digital oganization to aws."""

import datetime
import json
import pulumi
import pulumi_aws as aws
import re
from pulumi import Config, ResourceOptions, export, Output

#####################################################################################
# Create asterion aws organization and organizational units
#####################################################################################

# Class definition for org
class org:
    # Default constructor
    def __init__(self, name):
        self.name = name
        self.org = object
        self.rootid = object

    # Static method to create an aws organization
    def create_org(self):
        
        # Attempt to create an aws organization for this current account
        try:
            self.org = aws.organizations.Organization(
                self.name,
                aws_service_access_principals=[
                    "cloudtrail.amazonaws.com",
                    "config.amazonaws.com",
                    "account.amazonaws.com",
                ],
                feature_set="ALL",
                opts=pulumi.ResourceOptions(retain_on_delete=True))
            
            # Set the root id for the aws organization
            self.rootid = self.org.roots[0].id
        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'create_org()' method of the 'org' class")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Static method to check if an aws organization exists for this account
    def org_exists(self):

        # Attempt to create the organization
        try:
            self.create_org()
            self.rootid = self.org.roots[0].id

            # Check if the organization has any root accounts
            if self.rootid is None or self.rootid == "":
                return False
            else:
                return True

        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'org_exists()' method of the 'org' class")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))
            self.org = aws.organizations.get_organization()
            self.rootid = self.org.roots[0].id
            return True

# Obtain pulumi configuration file contents
config = Config()

# Create an aws object for the asterion-infra-aws organization
asterion_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_org.org_exists():
    asterion_org.create_org()
pulumi.export("asterion org id", asterion_org.org.id)
pulumi.export("asterion org root id", asterion_org.rootid)
pulumi.export("asterion org account id", asterion_org.org.master_account_id)

# Create asterion infra-aws organizational unit
asterion_infra_aws = aws.organizations.OrganizationalUnit(
    "asterion-infra-aws-ou", 
    parent_id=asterion_org.rootid,
    name="asterion-infra-aws-ou"
)

# Create asterion infra-aws environment ou's
asterion_infra_aws_dev = aws.organizations.OrganizationalUnit(
    "asterion-infra-aws-dev-ou",
    parent_id=asterion_infra_aws.id,
    name="asterion-infra-aws-dev-ou"
)
asterion_infra_aws_test = aws.organizations.OrganizationalUnit(
    "asterion-infra-aws-test-ou", 
    parent_id=asterion_infra_aws.id,
    name="asterion-infra-aws-test-ou"
)
asterion_infra_aws_prod = aws.organizations.OrganizationalUnit(
    "asterion-infra-aws-prod", 
    parent_id=asterion_infra_aws.id,
    name="asterion-infra-aws-prod-ou"
)

# Output asterion environment ou id's
pulumi.export("asterion dev ou id", asterion_infra_aws.id)
pulumi.export("asterion dev ou id", asterion_infra_aws_dev.id)
pulumi.export("asterion test ou id", asterion_infra_aws_test.id)
pulumi.export("asterion prod ou id", asterion_infra_aws_prod.id)

#####################################################################################

#####################################################################################
# Create asterion aws iam users
#####################################################################################

# Try to create an asterion iam group for administrative users
try:
    admin_group = aws.iam.Group(
        "asterion-admins",
        name="asterion-admins",
        path="/users/"
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-admins iam group")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Obtain dev stack iam usernames from pulumi configuration
new_usernames = config.require('newUsernames')

# Export the list of username strings
export("username string list", new_usernames)

# Split the usernames string into a list
usernames = re.split('[;,.\-\%]',str(new_usernames))

# Define a list of administrator users for later
administrators = []

# Create the asterion users
for name in usernames:

    # Try to create an iam user account
    try:
        new_user = aws.iam.User(
            "asterion-user-" + name,
            name=name,
            force_destroy=True
        )
    except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a new user: '" + str(name) + "'")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Try to create a login for the user
    try:
        new_user_login = aws.iam.UserLoginProfile(
            "asterion-user-login-" + name,
            user=name
        )
    except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a login profile for user: '" + str(name) + "'")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Export password for the user
    export("new user password for '" + name + "'", new_user_login.password)

    # Add the user to the list of administrators
    administrators.append(new_user.name.apply(lambda v:v))

# Add the users to the admin group
admin_team = aws.iam.GroupMembership(
    "asterion-admins-team-members",
    users=administrators,
    group=admin_group.name
)

#####################################################################################

# TODO: If wanting to make the stack tear down process 
# repeatable/automated, you will need to create a 
# conditional statement that checks if the accounts 
# exist in a "suspended account" OU first and obtain 
# those before creating new accounts.

#####################################################################################
# Create asterion aws accounts
#####################################################################################

# Try to create asterion infra-aws environment accounts
try:
    asterion_infra_aws_dev_acc = aws.organizations.Account(
        "asterion-dev-account",
        email="asterion-infra-aws-dev@asterion.digital",
        name="Asterion Infra-AWS Dev Team",
        parent_id=asterion_infra_aws_dev.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-dev account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

try:
    asterion_infra_aws_test_acc = aws.organizations.Account(
        "asterion-test-account",
        email="asterion-infra-aws-test@asterion.digital",
        name="Asterion Infra-AWS Test Team",
        parent_id=asterion_infra_aws_test.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-test account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

try:
    asterion_infra_aws_prod_acc = aws.organizations.Account(
        "asterion-prod-account",
        email="asterion-infra-aws-prod@asterion.digital",
        name="Asterion Infra-AWS Prod Team",
        parent_id=asterion_infra_aws_prod.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-prod account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Output asterion account id's
pulumi.export("asterion dev account id", asterion_infra_aws_dev_acc.id)
pulumi.export("asterion test account id", asterion_infra_aws_test_acc.id)
pulumi.export("asterion prod account id", asterion_infra_aws_prod_acc.id)

#####################################################################################

#####################################################################################
# Create and apply asterion aws iam user and role policies
#####################################################################################

# Create a policy document for the assumerole policies
assumerole_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=[
                "sts:AssumeRole"
            ],
            effect="Allow",
            resources=[
                Output.concat("arn:aws:iam::",asterion_infra_aws_dev_acc.id,":role/Administrator"),
                Output.concat("arn:aws:iam::",asterion_infra_aws_test_acc.id,":role/Administrator"),
                Output.concat("arn:aws:iam::",asterion_infra_aws_prod_acc.id,":role/Administrator")
            ]
        )
    ]
)

# Attach the assumerole policy document to the admins group policy
admin_group_assumerole_policy = aws.iam.GroupPolicy("asterion-group-admins-policy",
    group=admin_group.name,
    policy=assumerole_policy_document.json
)

#########################################################################################