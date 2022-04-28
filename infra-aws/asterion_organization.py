# Create a class that models the asterion aws organization
class org:

    # Default constructor
    def __init__(self, name, org):
        self.name = name
        self.org = org

    # Create an aws org for the current account
    def create_org(self):
        
        # Create an organization for this current account
        self.org = aws.organizations.Organization(self.name,
            aws_service_access_principals=[
                "cloudtrail.amazonaws.com",
                "config.amazonaws.com",
            ],
            feature_set="ALL")

    # Check if an aws org exists for this account
    def org_exists(self):
        if self.org.id == "" or self.org.id is none:
            return False
        else:
            return True