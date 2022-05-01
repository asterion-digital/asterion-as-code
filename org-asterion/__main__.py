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

# Blueprint for creating an aws asterion-ou object
class ou:

    # Default constructor
    def __init__(self, name, org, parentid):
        self.name = name
        self.org = org
        self.ou = ou
        self.parentid = parentid

    # Static method to create an aws organizational unit within the specified organization
    def create_ou(self):

        # Create an ou for the org
        self.ou = aws.organizations.OrganizationalUnit(
            self.name,
            parent_id=self.parentid
        )

# Create an aws object for the asterion-infra-aws organization
asterion_infra_aws_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_infra_aws_org.org_exists:
    asterion_infra_aws_org.create_org()
pulumi.export("Asterion aws org ID", asterion_infra_aws_org.org.id)
pulumi.export("Asterion aws org root ID", asterion_infra_aws_org.rootid)

# Create the asterion-infra-aws-ou object with the parent as root
asterion_infra_aws_ou = ou(
    'asterion-infra-aws-ou', 
    asterion_infra_aws_org.org, 
    asterion_infra_aws_org.rootid
    )

# Send the ou object to aws for creation
asterion_infra_aws_ou.create_ou()
pulumi.export(asterion_infra_aws_ou.name + " ID", asterion_infra_aws_ou.ou.id)

# Create the asterion-infra-aws-dev-ou object with asterion-infra-aws as the parent
asterion_infra_aws_dev_ou = ou(
    'asterion-infra-aws-dev-ou', 
    asterion_infra_aws_org.org, 
    asterion_infra_aws_ou.ou.id
    )

# Send the dev-ou object to aws for creation
asterion_infra_aws_dev_ou.create_ou()
pulumi.export(asterion_infra_aws_dev_ou.name + " ID", asterion_infra_aws_dev_ou.ou.id)

# Create the asterion-infra-aws-test-ou object with asterion-infra-aws as the parent
asterion_infra_aws_test_ou = ou(
    'asterion-infra-aws-test-ou', 
    asterion_infra_aws_org.org, 
    asterion_infra_aws_ou.ou.id
    )

# Send the test-ou object to aws for creation
asterion_infra_aws_test_ou.create_ou()
pulumi.export(asterion_infra_aws_test_ou.name + " ID", asterion_infra_aws_test_ou.ou.id)

# Create the asterion-infra-aws-prod-ou object with asterion-infra-aws as the parent
asterion_infra_aws_prod_ou = ou(
    'asterion-infra-aws-prod-ou', 
    asterion_infra_aws_org.org, 
    asterion_infra_aws_ou.ou.id
    )

# Send the prod-ou object to aws for creation
asterion_infra_aws_prod_ou.create_ou()
pulumi.export(asterion_infra_aws_prod_ou.name + " ID", asterion_infra_aws_prod_ou.ou.id)