#####################################################################################
# Create asterion aws iam users
#####################################################################################
import datetime
import pulumi
import pulumi_aws as aws
from pulumi import Config, ResourceOptions, export

# Obtain the pulumi configuration
config = Config()

# Try to create an asterion iam group for administrative users
try:
    admin_group = aws.iam.Group(
        "asterion-admins",
        name="asterion-admins",
        path="/users/"
    )
except BaseException as err:
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the asterion-admins iam group")
    pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

# Obtain dev stack iam usernames from pulumi configuration
usernames = config.require_object('iamUsersToAdd')

# Define a list of administrator usernames for later
administrators = []

# Define a list of administrator arns for later
arns = []

# Create the asterion users
for name in usernames["users"]:

    # Try to create an iam user account
    try:
        new_user = aws.iam.User(
            "asterion-user-" + name,
            name=name,
            force_destroy=True
        )
    except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a new user: '" + str(name) + "'")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Try to create a login for the user
    try:
        new_user_login = aws.iam.UserLoginProfile(
            "asterion-user-login-" + name,
            user=name
        )
    except BaseException as err:
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a login profile for user: '" + str(name) + "'")
            pulumi.log.info("PYLOGGER (" + str(datetime.datetime.now()) + "): " + str(err))

    # Export user information for the user
    export("new user password for '" + name + "'", new_user_login.password)

    # Add the user to the list of administrators
    administrators.append(new_user.name.apply(lambda v:v))

    # Add the user arn to the list of arns
    arns.append(new_user.arn.apply(lambda v:v))

# Add the users to the admin group
admin_team = aws.iam.GroupMembership(
    "asterion-admins-team-members",
    users=administrators,
    group=admin_group.name
)