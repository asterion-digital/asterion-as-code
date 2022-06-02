"""A pulumi program to deploy asterion-digital oganization to aws."""

# Update sys path to include modules library
import sys
sys.path.append('modules')
import account as awsaccount
import datetime
import org as awsorg
import ou as awsou
import policies as awspolicies
import pulumi
import pulumi_aws as aws
import pulumi_command as command
import users as awsusers
from pulumi import Config, ResourceOptions, export, Output, StackReference

# Obtain pulumi configuration file contents
config = Config()

# Set pulumi configuration values
stack_environment   =   pulumi.get_stack()
account_id          =   config.require("accountId")
groupname           =   config.require("iamGroupName")
usernames           =   config.require_object("iamUsersToAdd")
org_id              =   config.require("orgId")
root_id             =   config.require("rootId")

# Create an aws object for the asterion-infra-aws organization
asterion_org = awsorg.org('asterion-infra-aws', org_id)

# Check if the asterion aws organization object is set else set it
if not asterion_org.org_exists():
    asterion_org.create_org()

# Export the org/root/account ids
pulumi.export("asterion org id", asterion_org.org.id)
pulumi.export("asterion org root resource id", asterion_org.rootid)
pulumi.export("asterion org root account id", asterion_org.org.master_account_id)

# Create the asterion stack ou
asterion_infra_aws_stack_ou = awsou.create(str(stack_environment), asterion_org.rootid)

 # Output asterion environment ou id's
pulumi.export("asterion " + str(stack_environment) + " ou id", asterion_infra_aws_stack_ou.id)

# Create an aws object for the asterion iam users
asterion_users = awsusers.users(usernames, groupname, stack_environment)

# Create the users in aws
asterion_users.process_users(asterion_infra_aws_stack_ou)

# Create the iam group to hold the new users
asterion_users.create_group()

# Add the new users to the new group
asterion_users.add_users_to_group()

# Export the iam user arns
pulumi.export("new user arns", asterion_users.arns)

# Create an object for the stack aws account
asterion_account = awsaccount.account("Asterion Infra-AWS " + str(stack_environment.capitalize()) + " Team", str(stack_environment), asterion_infra_aws_stack_ou, account_id)

# Check if the asterion aws account exists
if not asterion_account.account_exists():

    # Stack aws account does not exist - create the asterion aws account
    asterion_account.create_account()

else:

    # Create the commands to move the existing aws account
    createcmd = Output.concat("aws organizations move-account --account-id ", account_id, " --source-parent-id ", asterion_org.rootid, " --destination-parent-id ", asterion_infra_aws_stack_ou.id)
    deletecmd = Output.concat("aws organizations move-account --account-id ", account_id, " --source-parent-id ", asterion_infra_aws_stack_ou.id, " --destination-parent-id ", asterion_org.rootid)
    
    # Stack aws account exists - move the existing account from root to stack parent ou
    try:
        movecmd = command.local.Command(
            "asterion-" + str(stack_environment) + "-move_account_cmd",
            create=createcmd.apply(lambda v:v),
            delete=deletecmd.apply(lambda v:v),
            opts=pulumi.ResourceOptions(
                depends_on=[asterion_infra_aws_stack_ou]
            )
        )
    except BaseException as err:
        pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to move the asterion-" + str(stack_environment) + " account")
        pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Create an aws iam assumerole policy and attach it to this account
awspolicies.create_attach_assumerole_policy([Output.concat("arn:aws:iam::", account_id, ":role/administrator")], groupname)


# Create a class to update the current stack account using the default role
class UpdateStackAccount:

    def assume_role_update_stack_account():

        # Create a provider that will assume the default `OrganizationAccountAccessRole` role in the asterion aws stack account
        provider = aws.Provider(
            "asterion-" + stack_environment + "-account-provider",
            assume_role=aws.ProviderAssumeRoleArgs(
                role_arn=Output.concat("arn:aws:iam::",asterion_account.account.id,":role/OrganizationAccountAccessRole"),
                session_name="PulumiSession",
                external_id="PulumiApplication"
            ),
            region=config.require('region')
        )

        # Define an inline policy document in the asterion dev account for resource permissions
        asterion_dev_policy_document = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "ec2:*"
                    ],
                    effect="Allow",
                    resources=[
                        Output.concat("arn:aws:ec2::",asterion_infra_aws_dev_acc.id,":*")
                    ]
                )
            ],
            opts=pulumi.InvokeOptions(provider=provider)
        )

        # Define a policy document that allows the administrator role to be assumed
        assume_role_policy_document = aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    actions=[
                        "sts:AssumeRole"
                    ],
                    effect="Allow",
                    principals=[
                        aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                            identifiers=[Output.concat("arn:aws:iam::",asterion_infra_aws_org.org.master_account_id,":user/administrator")],
                            type="AWS"
                        )
                    ]
                )
            ],
            opts=pulumi.InvokeOptions(provider=provider)
        )

        # Create a new role in the asterion dev account 
        admin_dev_role = aws.iam.Role(
            "asterion-dev-admin-role",
            assume_role_policy=assume_role_policy_document.json,
            inline_policies=[
                aws.iam.RoleInlinePolicyArgs(
                    name="asterion-dev-resource-policy",
                    policy=asterion_dev_policy_document.json
                )
            ],
            opts=pulumi.ResourceOptions(provider=provider)
        ) 