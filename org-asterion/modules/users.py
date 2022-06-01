#####################################################################################
# Create asterion iam users in aws
#####################################################################################
from concurrent.futures import ThreadPoolExecutor
import datetime
import pulumi
import pulumi_aws as aws
import pulumi_command as command
from pulumi import Config, ResourceOptions, export, Output

# Class definition for users
class users:

    # Default constructor
    def __init__(self, usernames, groupname, environment):
        self.arns = []
        self.environment = environment
        self.group = object
        self.groupmembership = object
        self.groupname = groupname
        self.output_usernames = []
        self.usernames = usernames

    def create_user(self, val, name, resource_dependency):

        # Check if the user doesn't exist
        if int(val) == 0:

            # User doesn't exist - try to create an iam user account
            try:
                new_user = aws.iam.User(
                    "asterion-new-user-" + name,
                    name=name,
                    force_destroy=True,
                    opts=pulumi.ResourceOptions(
                        depends_on=[resource_dependency]
                    )
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

            # Export user information to the stack
            export("new user password for '" + name + "'", new_user_login.password)
            export("user " + name + " id", new_user.unique_id)

            # Add the user to the list of administrators
            self.output_usernames.append(new_user.name.apply(lambda v:v))

            # Add the user arn to the list of arns
            self.arns.append(new_user.arn.apply(lambda v:v))

    # Static method to create the users from the provided iam list
    def process_users(self, resource_dependency):

        # Iterate through the list of usernames
        for name in self.usernames["users"]:
            
            # Interrogate the aws cli using the name to determine if the user already has an aws user id
            user_id = self.get_user_id_from_cli(name)

            # Create the user
            Output.all(user_id,name,resource_dependency).apply(lambda v: self.create_user(len(v[0]),v[1],v[2]))

    # Static method to create an iam group for the users
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

    # Static method to add the defined users to the defined group
    def add_users_to_group(self):

        # Add the users to the admin group
        self.groupmembership = aws.iam.GroupMembership(
            self.groupname + "-team-members",
            users=self.output_usernames,
            group=self.group.name
        )

    # Static method to check if a specific username already exists
    def get_user_id_from_cli(self, username):
        
        # Set a local pulumi command to obtain the unique aws user id from aws using the proposed username
        get_user_cmd = Output.concat("aws iam list-users --query \"Users[?UserName=='",username,"'].UserId\" --output text")

        # Try to run the local command to obtain the user's unique id
        try:
            user_awsid = command.local.Command(
                "asterion-" + str(self.environment) + "-get_user_" + username + "_cmd",
                create=get_user_cmd.apply(lambda v: v)
            )

            # Export the user id
            export("user " + username + " id", user_awsid.stdout)

        except BaseException as err:
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to check if user '" + username + "' exists")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

        # Return the output from the cli
        return user_awsid.stdout