"""A pulumi program to deploy asterion-digital infra on aws."""

# Import dependencies
import requests
import pulumi
import pulumi_aws as aws
import pulumi_command as command

# Initialise configuration
config = pulumi.Config()
public_key = config.require('publickey')
private_key = config.require_secret('privatekey')
extip = requests.get('http://checkip.amazonaws.com/')

# Stand up dedicated vpc and internet gateway
vpc = aws.ec2.Vpc("asterion-infra-vpc", cidr_block="10.0.0.0/16", enable_dns_hostnames=True)
igw = aws.ec2.InternetGateway("asterion-infra-igw", vpc_id=vpc.id)

# Create a public subnet and route table in the vpc
public_subnet = aws.ec2.Subnet(
	"asterion-infra-public-subnet",
	cidr_block="10.0.101.0/24",
    map_public_ip_on_launch=True,
	tags={ "Name": "asterion-infra-ec2" },
	vpc_id=vpc.id
)

route_table = aws.ec2.RouteTable(
	"asterion-infra-route-table",
	vpc_id=vpc.id,
	routes=[ { "cidr_block": "0.0.0.0/0", "gateway_id": igw.id } ]
)

# Associate the route table with the subnet
rt_assoc = aws.ec2.RouteTableAssociation(
	"asterion-infra-rta",
	route_table_id=route_table.id,
	subnet_id=public_subnet.id
)

# Create a security group to allow web traffic
sg = aws.ec2.SecurityGroup(
	"asterion-infra-sg",
	description="Allow http traffic to asterion infra",
    ingress=[
        { 'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': [extip.text.strip()+'/32'] },
        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 6443, 'to_port': 6443, 'cidr_blocks': [extip.text.strip()+'/32'] },
        { 'protocol': 'tcp', 'from_port': 6443, 'to_port': 6443, 'cidr_blocks': [public_subnet.cidr_block] },
    ],
    egress=[
        { 'protocol': 'tcp', 'from_port': 22, 'to_port': 22, 'cidr_blocks': [extip.text.strip()+'/32'] },
        { 'protocol': 'tcp', 'from_port': 80, 'to_port': 80, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 443, 'to_port': 443, 'cidr_blocks': ['0.0.0.0/0'] },
        { 'protocol': 'tcp', 'from_port': 6443, 'to_port': 6443, 'cidr_blocks': [extip.text.strip()+'/32'] },
        { 'protocol': 'tcp', 'from_port': 6443, 'to_port': 6443, 'cidr_blocks': [public_subnet.cidr_block] },
    ],
    vpc_id=vpc.id,
)

# Retrive the amazon ami for ubuntu
ami = aws.ec2.get_ami(
	most_recent="true",
	owners=["099720109477"],
	filters=[{"name": "name", "values": ["*ubuntu/images/hvm-ssd/ubuntu-focal-20.04-arm64*"]}]
)
pulumi.export("Infra server ami:", ami.name)

# Initialise a keypair for infra server instance based on configured public key
keypair = aws.ec2.KeyPair("asterion-infra-key", public_key=public_key)
pulumi.export("Keypair", keypair.key_name)

# Create asterion infra server instance
instance = aws.ec2.Instance(
	"asterion-infra-server",
    key_name=keypair.key_name,
	instance_type="t4g.small",
	vpc_security_group_ids=[sg.id],
	ami=ami.id,
    subnet_id=public_subnet.id,
    associate_public_ip_address=True,
)
pulumi.export("Infra server public ip", instance.public_ip)


# Setup a connection to the infra server instance
connection = command.remote.ConnectionArgs(host=instance.public_ip, user='ubuntu',private_key=private_key)

# Install required components
install_helm = command.remote.Command('asterion-infra-install-helm',
    connection=connection,
                                      create='curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash',
    opts=pulumi.ResourceOptions(depends_on=[instance]),
)

install_k3s = command.remote.Command('asterion-infra-install-k3s',
    connection=connection,
    create='curl -sfL https://get.k3s.io | sh -s - server --write-kubeconfig-mode 644 --no-deploy traefik --no-deploy servicelb > ~/.k3s_log.log',
    opts=pulumi.ResourceOptions(depends_on=[install_helm])
)

# Export the infra server commmand output
pulumi.export('Infra server helm stdout', install_helm.stdout)
pulumi.export('Infra server k3s stdout', install_k3s.stdout)
