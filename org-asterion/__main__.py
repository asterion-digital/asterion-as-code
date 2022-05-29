"""A pulumi program to deploy asterion-digital oganization to aws."""
import datetime
import pulumi
import pulumi_aws as aws
import pulumi_command as command
from pulumi import Config, ResourceOptions, export, Output

# Obtain pulumi configuration file contents
config = Config()

# Set pulumi configuration values
account_id      =   config.require("accountId")
environment     =   pulumi.get_stack()
org             =   config.require("currentOrgName")
parent_id       =   config.require("parentId")

# Get the current pulumi stack
stack = pulumi.StackReference(f"{org}/org-asterion/{environment}")

# Import the org classes from the org module
import org as awsorg

# Export the org/root/account ids
pulumi.export("asterion org id", awsorg.asterion_org.org.id)
pulumi.export("asterion org root resource id", awsorg.asterion_org.rootid)
pulumi.export("asterion org root account id", awsorg.asterion_org.org.master_account_id)

# Output asterion environment ou id's
pulumi.export("asterion ou id", awsorg.asterion_infra_aws.id)
pulumi.export("asterion dev ou id", awsorg.asterion_infra_aws_dev.id)
pulumi.export("asterion test ou id", awsorg.asterion_infra_aws_test.id)
pulumi.export("asterion prod ou id", awsorg.asterion_infra_aws_prod.id)

# Register the iam users with aws
import users as users

# Export the iam user arns
pulumi.export("new user arns", users.arns)

#####################################################################################

# TODO: If wanting to make the stack tear down process 
# repeatable/automated, you will need to create a 
# conditional statement that checks if the accounts 
# exist in a "suspended account" OU first and obtain 
# those before creating new accounts.

#####################################################################################
# Create asterion aws accounts
#####################################################################################

# Try to obtain an existing AWS account
try:
    existing_account = aws.organizations.Account.get(
        resource_name="Asterion Infra-AWS " + str(environment.capitalize()) + " Team",
        id=account_id
    )

    # Export the new dev aws account id
    pulumi.export("asterion " + str(environment) + " account id", existing_account.id)

except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found while trying to obtain the 'Asterion Infra-AWS " + str(environment.capitalize()) + " Team' account '" + account_id + "'")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Define an aws cli command that will move the asteriondev aws account from the root account to the dev ou
move_account_on_create_cmd=Output.concat("aws organizations move-account --account-id ", account_id, " --source-parent-id ", awsorg.asterion_org.rootid, " --destination-parent-id ",
awsorg.asterion_infra_aws_dev.id)

# Define an aws cli command that will move the asteriondev aws account from the dev ou to the root account
move_account_on_delete_cmd=Output.concat("aws organizations move-account --account-id ", account_id, " --source-parent-id ", awsorg.asterion_infra_aws_dev.id, " --destination-parent-id ",
awsorg.asterion_org.rootid)

# Attempt to move stack aws account depending on pulumi state
try:
    # Run the local command
    move_account= command.local.Command('asterion-' + str(environment) + "-move_account_cmd",
        create=move_account_on_create_cmd.apply(lambda v: v),
        delete=move_account_on_delete_cmd.apply(lambda v: v),
        opts=pulumi.ResourceOptions(depends_on=[awsorg.asterion_infra_aws_dev])
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found while trying to move the '" + str(environment) + "' account '" + account_id + "'")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Ensure the stack aws account id is up-to-date
account_id = stack.get_output("asterion " + environment + " account id")

# Determine if the stack's aws account exists by comparing the current stack id with the existing account id
account_exists = Output.all(existing_account.id, account_id).apply(
    lambda v: True if (v[0] == v[1]) else False)

# Try to create asterion infra-aws environment account if it doesn't exist
if not account_exists:
    try:
        asterion_infra_aws_acc = aws.organizations.Account(
            "asterion-" + str(environment) + "-account",
            email="asterion-infra-aws-" + str(environment) + "@asterion.digital",
            name="Asterion Infra-AWS " + str(environment.capitalize()) + " Team",
            parent_id=awsorg.asterion_infra_aws_dev.id,
            opts=pulumi.ResourceOptions(
                retain_on_delete=True,
                depends_on=[move_account]
            )
        )

        # Update the stack account id with the new aws id
        account_id = asterion_infra_aws_acc.id

    except BaseException as err:
        pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-" + str(environment) + " account")
        pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Export the stack aws account id
pulumi.export("asterion " + str(environment) + " account id ", account_id)

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
                Output.concat("arn:aws:iam::", account_id, ":role/administrator"),
            ]
        )
    ]
)

# Attach the assumerole policy document to the admins group policy
admin_group_assumerole_policy = aws.iam.GroupPolicy("asterion-group-admins-policy",
    group=users.admin_group.name,
    policy=assumerole_policy_document.json
)

#########################################################################################