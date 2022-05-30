#####################################################################################
# Create asterion iam users in aws
#####################################################################################
import datetime
import pulumi
import pulumi_aws as aws
from pulumi import Config, ResourceOptions, export

# Class definition for users
class users:

    # Default constructor
    def __init__(self, usernames, groupname):
        self.arns = []
        self.group = object
        self.groupmembership = object
        self.groupname = groupname
        self.output_usernames = []
        self.usernames = usernames

    # Create the users from the provided iam list
    def create_users(self):

        # Iterate through the list of usernames
        for name in self.usernames["users"]:

            # Try to create an iam user account
            try:
                new_user = aws.iam.User(
                    "asterion-user-" + name,
                    name=name,
                    force_destroy=True
                )
            except BaseException as err:
                    pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a new user: '" + str(name) + "'")
                    pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

            # Try to create a login for the user
            try:
                new_user_login = aws.iam.UserLoginProfile(
                    "asterion-user-login-" + name,
                    user=name,
                    opts=pulumi.ResourceOptions(
                        depends_on=[new_user]
                    )
                )
            except BaseException as err:
                    pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create a login profile for user: '" + str(name) + "'")
                    pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

            # Export user information for the user
            export("new user password for '" + name + "'", new_user_login.password)

            # Add the user to the list of administrators
            self.output_usernames.append(new_user.name.apply(lambda v:v))

            # Add the user arn to the list of arns
            self.arns.append(new_user.arn.apply(lambda v:v))
        
    # Create an iam group for the users
    def create_group(self):

        # Try to create an asterion iam group for administrative users
        try:
            self.group = aws.iam.Group(
                self.groupname,
                name=self.groupname,
                path="/users/"
            )

        except BaseException as err:
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the '" + self.groupname + "' iam group")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

    # Add the defined users to the defined group
    def add_users_to_group(self):

        # Add the users to the admin group
        self.groupmembership = aws.iam.GroupMembership(
            self.groupname + "-team-members",
            users=self.output_usernames,
            group=self.group.name
        )