#####################################################################################
# Create an asterion aws account for this stack
#####################################################################################
import pulumi
import pulumi_aws as aws
import datetime
from pulumi import ResourceOptions, Output

# Class definition for org
class account:

    # Default constructor
    def __init__(self, name, environment, ou, account_id):
        self.account = object
        self.account_id = account_id
        self.environment = environment
        self.name = name
        self.parent_ou = ou

    # Static method to create an aws organization
    def create_account(self):
        
        # Attempt to create a new aws account
        try:
            self.account = aws.organizations.Account(
                "asterion-" + str(self.environment) + "-account",
                email="asterion-infra-aws-" + str(self.environment) + "@asterion.digital",
                name="Asterion Infra-AWS " + str(self.environment.capitalize()) + " Team",
                parent_id=self.parent_ou.id,
                opts=pulumi.ResourceOptions(
                    retain_on_delete=True
                )
            )

            # Update the stack account id with the new aws id
            self.account_id = self.account.id

            # Export the new stack aws account id
            pulumi.export("asterion " + str(self.environment) + " account id ", self.account_id)

        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-" + str(self.environment) + " account")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Static method to check if an aws organization exists for this account
    def account_exists(self):

        # Try to obtain an existing AWS account
        try:
            self.account = aws.organizations.Account.get(
                resource_name=self.name,
                id=self.account_id
            )

            # Check if the account already exists
            if Output.all(self.account.id, self.account_id).apply(lambda v: True if (v[0] == v[1]) else False):

                # Export the dev aws account id
                pulumi.export("asterion " + str(self.environment) + " account id", self.account.id)
                return True

            else:
                return False

        except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found while trying to obtain the 'Asterion Infra-AWS " + str(self.environment.capitalize()) + " Team' account '" + str(self.account_id) + "'")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))
