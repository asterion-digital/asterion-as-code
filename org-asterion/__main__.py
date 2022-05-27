"""A pulumi program to deploy asterion-digital oganization to aws."""
import datetime
import pulumi
import pulumi_aws as aws
from pulumi import Config, ResourceOptions, export, Output

# Obtain pulumi configuration file contents
config = Config()

# Import the org classes from the org module
import org as awsorg

# Export the org/root/account ids
pulumi.export("asterion org id", awsorg.asterion_org.org.id)
pulumi.export("asterion org root id", awsorg.asterion_org.rootid)
pulumi.export("asterion org account id", awsorg.asterion_org.org.master_account_id)

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

# Try to create asterion infra-aws environment accounts
try:
    asterion_infra_aws_dev_acc = aws.organizations.Account(
        "asterion-dev-account",
        email="asterion-infra-aws-dev@asterion.digital",
        name="Asterion Infra-AWS Dev Team",
        parent_id=awsorg.asterion_infra_aws_dev.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-dev account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

try:
    asterion_infra_aws_test_acc = aws.organizations.Account(
        "asterion-test-account",
        email="asterion-infra-aws-test@asterion.digital",
        name="Asterion Infra-AWS Test Team",
        parent_id=awsorg.asterion_infra_aws_test.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-test account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

try:
    asterion_infra_aws_prod_acc = aws.organizations.Account(
        "asterion-prod-account",
        email="asterion-infra-aws-prod@asterion.digital",
        name="Asterion Infra-AWS Prod Team",
        parent_id=awsorg.asterion_infra_aws_prod.id,
        opts=pulumi.ResourceOptions(retain_on_delete=True)
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-prod account")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Output asterion account id's
pulumi.export("asterion dev account id", asterion_infra_aws_dev_acc.id)
pulumi.export("asterion test account id", asterion_infra_aws_test_acc.id)
pulumi.export("asterion prod account id", asterion_infra_aws_prod_acc.id)

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
                Output.concat("arn:aws:iam::",asterion_infra_aws_dev_acc.id,":role/administrator"),
                Output.concat("arn:aws:iam::",asterion_infra_aws_test_acc.id,":role/administrator"),
                Output.concat("arn:aws:iam::",asterion_infra_aws_prod_acc.id,":role/administrator")
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