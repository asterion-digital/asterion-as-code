"""A pulumi program to deploy asterion-digital oganization to aws."""

import pulumi
import pulumi_aws as aws

# Blueprint for creating an aws asterion-org object
class org:

    # Default constructor
    def __init__(self, name):
        self.name = name
        self.org = aws.organizations.get_organization()

    # Create an aws organization for the current account
    def create_org(self):
        
        # Create an aws organization for this current account
        self.org = aws.organizations.Organization(self.name,
            aws_service_access_principals=[
                "cloudtrail.amazonaws.com",
                "config.amazonaws.com",
            ],
            feature_set="ALL")

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
pulumi.export("Asterion aws org ID", asterion_infra_aws_org.org.id)