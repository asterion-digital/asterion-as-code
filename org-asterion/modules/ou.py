#####################################################################################
# Create an asterion aws organization unit for the stack
#####################################################################################
import pulumi
import pulumi_aws as aws
import datetime

# Static method to create an organizational unit in aws
def create(name, parentid):

    # Attempt to create the organization
    try:
        # Create asterion infra-aws organizational unit
        ou = aws.organizations.OrganizationalUnit(
            "asterion-infra-aws" + name + "-ou", 
            parent_id=parentid,
            name="asterion-infra-aws" + name + "-ou"
        )

        # Send back the ou pulumi output object
        return ou

    except BaseException as err:
        pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found in the 'create()' method of the 'ou.py' module")
        pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))