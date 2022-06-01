#####################################################################################
# Create an asterion aws organization unit for the stack
#####################################################################################
import pulumi
import pulumi_aws as aws
import datetime
import pulumi_command as command
from pulumi import ResourceOptions, Config, Output, export

# Static method to create an organizational unit in aws
def create_ou(id_len, parent_id, environment, resource_dependency):
    pulumi.log.info(str(id_len))
    # Check if the ou exists
    if int(id_len) == 0:
        pulumi.log.info("FIRST OU")

        # Attempt to create the main organizational unit
        try:
            main_ou = aws.organizations.OrganizationalUnit(
                "asterion-infra-aws-ou", 
                parent_id=parent_id,
                name="asterion-infra-aws-ou"
            )

            # Output asterion main ou id
            pulumi.export("asterion " + str(environment) + " ou id", main_ou.id)

        except BaseException as err:
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the MAIN ou in the 'create_ou()' method of the 'ou.py' module")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))
        
        # Send the main ou object back
        return main_ou

    # Check if the main ou exists
    elif int(id_len) > 0:
        
        # Check if the stack ou exists


        # Attempt to create the stack organizational unit
        try: 
            stack_ou = aws.organizations.OrganizationalUnit(
                "asterion-infra-aws-" + pulumi.get_stack() + "-ou", 
                parent_id=parent_id,
                name="asterion-infra-aws-" + pulumi.get_stack() + "-ou",
                opts=pulumi.ResourceOptions(
                    depends_on=[resource_dependency]
                )
            )

        except BaseException as err:
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to create the STACK ou in the 'create_ou()' method of the 'ou.py' module")
            pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

        # Send the stack ou object back
        return stack_ou

# Static method to check if a specific username already exists
def get_ou_id_from_cli(parent_id, environment, resource_dependency):
    
    # Determine the command to use
    if resource_dependency == "":

        # Set a local pulumi command to obtain the unique aws ou id from aws using the proposed username
        get_ou_cmd = Output.concat("aws organizations list-organizational-units-for-parent --parent-id ", parent_id, " --query \"OrganizationalUnits[?Name=='asterion-infra-aws-ou'].Id\" --output text")
    
    else:
        
        # Set a local pulumi command to obtain the unique aws ou id from aws using the proposed username
        get_ou_cmd = Output.concat("aws organizations list-organizational-units-for-parent --parent-id ", parent_id, " --query \"OrganizationalUnits[?Name=='asterion-infra-aws-", environment,"-ou'].Id\" --output text")

    # Try to run the local command to obtain the user's unique id
    try:
        ou_awsid = command.local.Command(
            "asterion-" + str(pulumi.get_stack()) + "-get_ou_" + str(environment) + "_cmd",
            create=get_ou_cmd.apply(lambda v: v)
        )

        # Export the user id
        export(environment + " ou id", ou_awsid.stdout)

    except BaseException as err:
        pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): There was a critical exception found trying to check if stack out for '" + environment + "' exists")
        pulumi.log.info("pylogger (" + str(datetime.datetime.now()) + "): " + str(err))

    # Return the output from the cli
    return ou_awsid

# Handle creation of the stack ou
def process_ou(environment, parent_id, resource_dependency, active):

    # Interrogate the aws cli using the name to determine if the ou already has an aws ou id
    ou_id = Output.all(parent_id, environment, resource_dependency).apply(lambda v: get_ou_id_from_cli(v[0],v[1],v[2]))
    
    # Create the ou
    return Output.all(ou_id.stdout, parent_id).apply(lambda v: create_ou(len(v[0]),v[1], environment, resource_dependency))