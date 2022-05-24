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

        # Attempt to obtain the organization
        try:
            self.org = aws.organizations.get_organization()
            self.rootid = self.org.roots[0].id

            # Check if the organization has any root accounts
            if self.rootid is None or self.rootid == "":
                return False
            else:
                return True

        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'org_exists()' method of the 'org' class")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))
            return False

# Obtain pulumi configuration file contents
config = Config()

# Obtain the aws pulumi configuration file contents
aws_config = Config("aws")

# Obtain dev stack iam username from pulumi config file
new_username = config.require('newUsername')

# Create an aws object for the asterion-infra-aws organization
asterion_infra_aws_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_infra_aws_org.org_exists():
    asterion_infra_aws_org.create_org()
pulumi.export("Asterion aws org id", asterion_infra_aws_org.org.id)
pulumi.export("Asterion aws org root id", asterion_infra_aws_org.rootid)
pulumi.export("Asterion aws org account id", asterion_infra_aws_org.org.master_account_id)

# Create asterion infra-aws organizational unit
asterion_infra_aws = aws.organizations.OrganizationalUnit("asterion-infra-aws", parent_id=asterion_infra_aws_org.rootid)

# Create asterion infra-aws environment ou's
asterion_infra_aws_dev = aws.organizations.OrganizationalUnit("asterion-infra-aws-dev", parent_id=asterion_infra_aws.id)
asterion_infra_aws_test = aws.organizations.OrganizationalUnit("asterion-infra-aws-test", parent_id=asterion_infra_aws.id)
asterion_infra_aws_prod = aws.organizations.OrganizationalUnit("asterion-infra-aws-prod", parent_id=asterion_infra_aws.id)

# Output asterion environment ou id's
pulumi.export("asterion-infra-aws OU ID", asterion_infra_aws.id)
pulumi.export("Dev OU ID", asterion_infra_aws_dev.id)
pulumi.export("Test OU ID", asterion_infra_aws_test.id)
pulumi.export("Prod OU ID", asterion_infra_aws_prod.id)

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

# Export password for the user
export("New user password", new_user_login.password)

# Add the users to the admin group
admin_team = aws.iam.GroupMembership(
    "asterion-admin-team",
    users=[
        new_user.name,
        "administrator"
    ],
    group=admin_group.name
)

# TODO: If wanting to make the stack tear down process 
# repeatable/automated, you will need to create a 
# conditional statement that checks if the accounts 
# exist in a "suspended account" OU first and obtain 
# those before creating new accounts.

# Try to create asterion infra-aws environment accounts
try:
    asterion_infra_aws_dev_acc = aws.organizations.Account(
        "asterion-infra-aws-dev-team",
        email="devRRN8XsdN9wHjpYD4KxW9sLx7@asterion.digital",
        name="Asterion Infra-AWS Dev Team",
        parent_id=asterion_infra_aws_dev.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
    asterion_infra_aws_test_acc = aws.organizations.Account(
        "asterion-infra-aws-test-team",
        email="testn6beRpTPbZ4j8JiX5CLX6xvH2@asterion.digital",
        name="Asterion Infra-AWS Test Team",
        parent_id=asterion_infra_aws_test.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
    asterion_infra_aws_prod_acc = aws.organizations.Account(
        "asterion-infra-aws-prod-team",
        email="prodmBJxpyCjBqcW8xhMwdfBkhtH@asterion.digital",
        name="Asterion Infra-AWS Prod Team",
        parent_id=asterion_infra_aws_prod.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )

# If there was an error E.G the accounts already exist then log the error
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found in 'main()'")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Output asterion environment account id's
pulumi.export("Dev Account ID", asterion_infra_aws_dev_acc.id)
pulumi.export("Test Account ID", asterion_infra_aws_test_acc.id)
pulumi.export("Production Account ID", asterion_infra_aws_prod_acc.id)

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

# Create a provider that will assume the default `OrganizationAccountAccessRole` role in the asterion dev account
provider = aws.Provider(
    "asterion-dev-account-provider",
    assume_role=aws.ProviderAssumeRoleArgs(
        role_arn=Output.concat("arn:aws:iam::",asterion_infra_aws_dev_acc.id,":role/OrganizationAccountAccessRole"),
        session_name="PulumiSession",
        external_id="PulumiApplication"
    ),
    region=aws_config.require('region')
)

#########################################################################################
# Apply configurations to asterion-dev aws account below
#########################################################################################

# Define an inline policy document in the asterion dev account for resource permissions
asterion_dev_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=[
                "ec2:*"
            ],
            effect="Allow",
            resources=[
                Output.concat("arn:aws:ec2::",asterion_infra_aws_dev_acc.id,":*")
            ]
        )
    ],
    opts=pulumi.InvokeOptions(provider=provider)
)

# Define a policy document that allows the administrator role to be assumed
assume_role_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            actions=[
                "sts:AssumeRole"
            ],
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    identifiers=[Output.concat("arn:aws:iam::",asterion_infra_aws_org.org.master_account_id,":user/administrator")],
                    type="AWS"
                )
            ]
        )
    ],
    opts=pulumi.InvokeOptions(provider=provider)
)

# Create a new role in the asterion dev account 
admin_dev_role = aws.iam.Role(
    "asterion-dev-admin-role",
    assume_role_policy=assume_role_policy_document.json,
    inline_policies=[
        aws.iam.RoleInlinePolicyArgs(
            name="asterion-dev-resource-policy",
            policy=asterion_dev_policy_document.json
        )
    ],
    opts=pulumi.ResourceOptions(provider=provider)
)