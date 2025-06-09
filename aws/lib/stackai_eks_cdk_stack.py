"""
StackAI EKS CDK Stack

This is the main CDK stack that orchestrates all constructs to create
a complete AWS infrastructure for running StackAI with Supabase on EKS.

Architecture:
- VPC with public/private subnets
- Aurora Serverless v2 (PostgreSQL) for Supabase
- DocumentDB for MongoDB workloads
- ElastiCache Redis for caching
- S3 for storage
- EKS cluster with managed node groups
- Supabase services deployed on Kubernetes
- ALB for ingress traffic
- API Gateway + Lambda for Edge Functions
"""
from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
    Tags
)

from .constructs.base_infrastructure import BaseInfrastructure
from .constructs.managed_services import ManagedServices
from .constructs.eks_cluster import EksCluster
from .constructs.supabase import SupabaseServices


class StackaiEksCdkStack(Stack):
    """Main CDK stack for StackAI on AWS EKS"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create base infrastructure (VPC, subnets, security groups)
        self.infrastructure = BaseInfrastructure(
            self, "BaseInfrastructure"
        )

        # 2. Create managed AWS services (RDS, DocumentDB, ElastiCache, S3)
        self.managed_services = ManagedServices(
            self, "ManagedServices",
            infrastructure=self.infrastructure
        )

        # 3. Create EKS cluster with node groups and add-ons
        self.eks_cluster = EksCluster(
            self, "EksCluster",
            infrastructure=self.infrastructure,
            managed_services=self.managed_services
        )

        # 4. Deploy Supabase services to EKS
        self.supabase_services = SupabaseServices(
            self, "SupabaseServices",
            infrastructure=self.infrastructure,
            managed_services=self.managed_services,
            eks_cluster=self.eks_cluster
        )

        # Add tags to all resources
        self._add_common_tags()

        # Create stack-level outputs
        self._create_stack_outputs()

    def _add_common_tags(self) -> None:
        """Add common tags to all resources in the stack"""
        
        Tags.of(self).add("Project", "StackAI")
        Tags.of(self).add("Environment", "Production")
        Tags.of(self).add("Owner", "StackAI-Team")
        Tags.of(self).add("ManagedBy", "CDK")
        Tags.of(self).add("CostCenter", "Engineering")
        Tags.of(self).add("Version", "1.0.0")

    def _create_stack_outputs(self) -> None:
        """Create high-level outputs for the entire stack"""
        
        # Connection information for external access
        CfnOutput(
            self, "StackAI-QuickStart",
            value=(
                f"1. Configure kubectl: aws eks update-kubeconfig --region {self.region} --name {self.eks_cluster.cluster.cluster_name}\n"
                f"2. Check pods: kubectl get pods -n supabase\n"
                f"3. Get ALB URL: kubectl get ingress -n supabase\n"
                f"4. Edge Functions URL: {self.supabase_services.edge_api.url}"
            ),
            description="Quick start commands to access your StackAI deployment"
        )
        
        CfnOutput(
            self, "ImportantEndpoints",
            value=(
                f"Aurora: {self.managed_services.aurora_cluster.cluster_endpoint.hostname}\n"
                f"DocumentDB: {self.managed_services.docdb_cluster.attr_endpoint}\n"
                f"Redis: {self.managed_services.redis_cluster.attr_configuration_end_point_address}\n"
                f"S3 Bucket: {self.managed_services.storage_bucket.bucket_name}\n"
                f"Edge Functions: {self.supabase_services.edge_api.url}"
            ),
            description="Important service endpoints"
        )
        
        # Debugging information
        CfnOutput(
            self, "DebuggingInfo",
            value=(
                f"VPC ID: {self.infrastructure.vpc.vpc_id}\n"
                f"Cluster Name: {self.eks_cluster.cluster.cluster_name}\n"
                f"Region: {self.region}\n"
                f"Account: {self.account}"
            ),
            description="Information for debugging and troubleshooting"
        )

    @property
    def cluster_info(self):
        """Return cluster information for external access"""
        return self.eks_cluster.get_cluster_info()

    @property
    def service_endpoints(self):
        """Return all service endpoints"""
        return {
            **self.managed_services.get_connection_info(),
            **self.supabase_services.get_service_info(),
            "cluster": self.cluster_info
        } 