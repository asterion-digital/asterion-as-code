"""A pulumi program to deploy asterion-digital oganization to aws."""

import pulumi
import pulumi_aws as aws

# Blueprint for creating an aws asterion-org object
class org:

    # Default constructor
    def __init__(self, name, org):
        self.name = name
        self.org = org

    # Create an aws org for the current account
    def create_org(self):
        
        # Create an organization for this current account
        self.org = aws.organizations.Organization(self.name,
            aws_service_access_principals=[
                "cloudtrail.amazonaws.com",
                "config.amazonaws.com",
            ],
            feature_set="ALL")

    # Check if an aws org exists for this account
    def org_exists(self):
        if self.org.id == "" or self.org.id is none:
            return False
        else:
            return True

# Create an aws org object for asterion-infra-aws
organization = org(
    'asterion-infra-aws',
    aws.organizations.get_organization())

# Check if the org object is set else set it
if not organization.org_exists:
    organization.create_org()
pulumi.export("Asterion aws org ID", organization.org.id)