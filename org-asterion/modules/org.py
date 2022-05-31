#####################################################################################
# Create asterion aws organization
#####################################################################################
import pulumi
import pulumi_aws as aws
import datetime
from pulumi import ResourceOptions, Config, Output

# Class definition for org
class org:

    # Default constructor
    def __init__(self, name, org_id):
        self.config = Config()
        self.name = name
        self.org = object
        self.org_id = org_id
        self.rootid = self.config.require("rootId")

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
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'create_org()' method of the 'org' class")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

    # Static method to check if an aws organization exists for this account
    def org_exists(self):

        # Attempt to obtain the organization
        try:
            self.org = aws.organizations.Organization.get(
                "asterion-organization",
                id=self.org_id
            )

            # Check if the organization has any root accounts
            if Output.all(self.org.id, self.org_id).apply(lambda v: True if (v[0] == v[1]) else False):
                
                # Try to set the root id of the org
                self.rootid = self.org.roots[0].id
                return True
            else:
                return False

        except BaseException as err:
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'org_exists()' method of the 'org' class")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))
            return True