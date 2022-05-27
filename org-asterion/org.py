#####################################################################################
# Create asterion aws organization
#####################################################################################
import pulumi
import pulumi_aws as aws
import datetime
from pulumi import ResourceOptions

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

# Create an aws object for the asterion-infra-aws organization
asterion_org = org('asterion-infra-aws')

# Check if the asterion aws organization object is set else set it
if not asterion_org.org_exists():
    asterion_org.create_org()

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