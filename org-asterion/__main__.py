"""A pulumi program to deploy asterion-digital oganization to aws."""

import pulumi
import pulumi_aws as aws

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
new_acc = aws.organizations.Account(
    "Test account", email="test@asterion.digital", name="Test Account", parent_id=asterion_infra_aws.id
)

# Output data about the new account
pulumi.export("Test Account id", new_acc.id)
pulumi.export("Test Account name", new_acc.name)
pulumi.export("Test Account email", new_acc.email)
pulumi.export("Test Account role", new_acc.role_name)