"""
Base Infrastructure Construct

This construct creates the foundational AWS infrastructure components:
- VPC with public and private subnets
- Security groups for different tiers
- Internet Gateway and NAT Gateway
- Route tables and routing
"""
from typing import List
from constructs import Construct
from aws_cdk import (
    aws_ec2 as ec2,
    CfnOutput
)


class BaseInfrastructure(Construct):
    """Base infrastructure construct for VPC and networking"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC with public and private subnets across 2 AZs
        self.vpc = ec2.Vpc(
            self, "StackAiVpc",
            max_azs=2,
            nat_gateways=1,  # Cost optimization: single NAT gateway
            subnet_configuration=[
                # Public subnets for ALB and bastion hosts
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                # Private subnets for EKS, RDS, ElastiCache, DocumentDB
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        
        # Create security groups
        self._create_security_groups()
        
        # Output VPC information
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for StackAI infrastructure"
        )
        
        CfnOutput(
            self, "VpcCidr",
            value=self.vpc.vpc_cidr_block,
            description="VPC CIDR block"
        )
    
    def _create_security_groups(self) -> None:
        """Create security groups for different application tiers"""
        
        # Security group for EKS cluster
        self.eks_cluster_sg = ec2.SecurityGroup(
            self, "EksClusterSG",
            vpc=self.vpc,
            description="Security group for EKS cluster control plane",
            allow_all_outbound=True
        )
        
        # Security group for EKS nodes
        self.eks_nodes_sg = ec2.SecurityGroup(
            self, "EksNodesSG",
            vpc=self.vpc,
            description="Security group for EKS worker nodes",
            allow_all_outbound=True
        )
        
        # Allow communication between cluster and nodes
        self.eks_cluster_sg.add_ingress_rule(
            peer=self.eks_nodes_sg,
            connection=ec2.Port.tcp(443),
            description="Allow nodes to communicate with cluster API server"
        )
        
        self.eks_nodes_sg.add_ingress_rule(
            peer=self.eks_cluster_sg,
            connection=ec2.Port.tcp_range(1025, 65535),
            description="Allow cluster to communicate with nodes"
        )
        
        # Allow node-to-node communication
        self.eks_nodes_sg.add_ingress_rule(
            peer=self.eks_nodes_sg,
            connection=ec2.Port.all_traffic(),
            description="Allow nodes to communicate with each other"
        )
        
        # Security group for RDS (PostgreSQL)
        self.rds_sg = ec2.SecurityGroup(
            self, "RdsSG",
            vpc=self.vpc,
            description="Security group for Aurora PostgreSQL",
            allow_all_outbound=False
        )
        
        self.rds_sg.add_ingress_rule(
            peer=self.eks_nodes_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow EKS nodes to connect to PostgreSQL"
        )
        
        # Security group for DocumentDB (MongoDB)
        self.docdb_sg = ec2.SecurityGroup(
            self, "DocDbSG",
            vpc=self.vpc,
            description="Security group for DocumentDB",
            allow_all_outbound=False
        )
        
        self.docdb_sg.add_ingress_rule(
            peer=self.eks_nodes_sg,
            connection=ec2.Port.tcp(27017),
            description="Allow EKS nodes to connect to DocumentDB"
        )
        
        # Security group for ElastiCache (Redis)
        self.redis_sg = ec2.SecurityGroup(
            self, "RedisSG",
            vpc=self.vpc,
            description="Security group for ElastiCache Redis",
            allow_all_outbound=False
        )
        
        self.redis_sg.add_ingress_rule(
            peer=self.eks_nodes_sg,
            connection=ec2.Port.tcp(6379),
            description="Allow EKS nodes to connect to Redis"
        )
        
        # Security group for ALB
        self.alb_sg = ec2.SecurityGroup(
            self, "AlbSG",
            vpc=self.vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True
        )
        
        # Allow HTTP and HTTPS traffic to ALB
        self.alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic from internet"
        )
        
        self.alb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS traffic from internet"
        )
        
        # Allow ALB to communicate with EKS nodes
        self.eks_nodes_sg.add_ingress_rule(
            peer=self.alb_sg,
            connection=ec2.Port.tcp_range(30000, 32767),
            description="Allow ALB to reach NodePort services"
        )
    
    @property
    def private_subnets(self) -> List[ec2.ISubnet]:
        """Return private subnets for database and cache deployments"""
        return self.vpc.private_subnets
    
    @property
    def public_subnets(self) -> List[ec2.ISubnet]:
        """Return public subnets for ALB deployment"""
        return self.vpc.public_subnets 