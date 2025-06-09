"""
EKS Cluster Construct

This construct creates and configures the Amazon EKS cluster:
- EKS cluster with proper IAM roles
- Managed node groups with auto-scaling
- AWS Load Balancer Controller add-on
- Cluster autoscaler
- CoreDNS and kube-proxy add-ons
- IAM roles for service accounts (IRSA)
"""
from typing import Dict, Any
from constructs import Construct
from aws_cdk import (
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    CfnOutput
)
from .base_infrastructure import BaseInfrastructure
from .managed_services import ManagedServices


class EksCluster(Construct):
    """Construct for Amazon EKS cluster and related resources"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        infrastructure: BaseInfrastructure,
        managed_services: ManagedServices,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.infrastructure = infrastructure
        self.managed_services = managed_services
        
        # Create IAM roles
        self._create_iam_roles()
        
        # Create EKS cluster
        self._create_cluster()
        
        # Add managed node groups
        self._add_node_groups()
        
        # Install essential add-ons
        self._install_addons()
        
        # Create service accounts with IRSA
        self._create_service_accounts()
        
        # Create outputs
        self._create_outputs()
    
    def _create_iam_roles(self) -> None:
        """Create IAM roles for EKS cluster and workers"""
        
        # EKS cluster service role
        self.cluster_role = iam.Role(
            self, "EksClusterRole",
            assumed_by=iam.ServicePrincipal("eks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy")
            ]
        )
        
        # Add additional permissions for EKS cluster operations
        self.cluster_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:DescribeAccountAttributes",
                    "ec2:DescribeAddresses",
                    "ec2:DescribeInternetGateways",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams"
                ],
                resources=["*"]
            )
        )
        
        # EKS node group role
        self.nodegroup_role = iam.Role(
            self, "EksNodeGroupRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
            ]
        )
        
        # Add CloudWatch permissions for container insights
        self.nodegroup_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "ec2:DescribeVolumes",
                    "ec2:DescribeTags",
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:DescribeLogGroups"
                ],
                resources=["*"]
            )
        )
        
        # Add additional permissions for EKS node operations
        self.nodegroup_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage"
                ],
                resources=["*"]
            )
        )
    
    def _create_cluster(self) -> None:
        """Create the EKS cluster"""
        
        # Add comprehensive Lambda permissions to cluster role to fix lambda:GetFunction errors
        # This resolves the issue where CDK's kubectl provider Lambda functions can't call each other
        self.cluster_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:GetFunction",
                    "lambda:InvokeFunction", 
                    "lambda:GetFunctionConfiguration",
                    "lambda:UpdateFunctionConfiguration",
                    "lambda:ListFunctions"
                ],
                resources=["*"]
            )
        )
        
        self.cluster = eks.Cluster(
            self, "StackAiEksCluster",
            version=eks.KubernetesVersion.V1_28,
            vpc=self.infrastructure.vpc,
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
            default_capacity=0,  # We'll add managed node groups explicitly
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
            role=self.cluster_role,
            security_group=self.infrastructure.eks_cluster_sg,
            output_cluster_name=True,
            output_config_command=True,
            cluster_logging=[
                eks.ClusterLoggingTypes.API,
                eks.ClusterLoggingTypes.AUDIT,
                eks.ClusterLoggingTypes.AUTHENTICATOR,
                eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                eks.ClusterLoggingTypes.SCHEDULER
            ]
        )
        
        # Enable encryption for EKS secrets
        self.cluster.add_manifest("EncryptionConfig", {
            "apiVersion": "v1",
            "kind": "EncryptionConfiguration",
            "resources": [
                {
                    "resources": ["secrets"],
                    "providers": [
                        {
                            "kms": {
                                "name": "alias/eks-encryption-key",
                                "cachesize": 1000
                            }
                        },
                        {
                            "identity": {}
                        }
                    ]
                }
            ]
        })
    

    
    def _add_node_groups(self) -> None:
        """Add managed node groups to the cluster"""
        
        # Primary node group for general workloads
        self.primary_nodegroup = self.cluster.add_nodegroup_capacity(
            "PrimaryNodeGroup",
            instance_types=[
                ec2.InstanceType("t3.large"),
                ec2.InstanceType("t3.xlarge")
            ],
            min_size=2,
            max_size=10,
            desired_size=3,
            disk_size=100,
            ami_type=eks.NodegroupAmiType.AL2_X86_64,
            capacity_type=eks.CapacityType.ON_DEMAND,
            node_role=self.nodegroup_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            tags={
                "Name": "StackAI-Primary-Node",
                "kubernetes.io/cluster/stackai-eks-cluster": "owned",
                "k8s.io/cluster-autoscaler/enabled": "true",
                "k8s.io/cluster-autoscaler/stackai-eks-cluster": "owned"
            }
        )
        
        # Spot instances node group for cost optimization
        self.spot_nodegroup = self.cluster.add_nodegroup_capacity(
            "SpotNodeGroup",
            instance_types=[
                ec2.InstanceType("t3.medium"),
                ec2.InstanceType("t3.large"),
                ec2.InstanceType("m5.large")
            ],
            min_size=0,
            max_size=5,
            desired_size=1,
            disk_size=50,
            ami_type=eks.NodegroupAmiType.AL2_X86_64,
            capacity_type=eks.CapacityType.SPOT,
            node_role=self.nodegroup_role,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            taints=[
                eks.TaintSpec(
                    key="spot-instance",
                    value="true",
                    effect=eks.TaintEffect.NO_SCHEDULE
                )
            ],
            tags={
                "Name": "StackAI-Spot-Node",
                "kubernetes.io/cluster/stackai-eks-cluster": "owned",
                "k8s.io/cluster-autoscaler/enabled": "true",
                "k8s.io/cluster-autoscaler/stackai-eks-cluster": "owned",
                "k8s.io/cluster-autoscaler/node-template/taint/spot-instance": "true:NoSchedule"
            }
        )
    
    def _install_addons(self) -> None:
        """Install essential EKS add-ons"""
        
        # AWS Load Balancer Controller
        self.alb_controller = eks.AlbController(
            self, "AlbController",
            cluster=self.cluster,
            version=eks.AlbControllerVersion.V2_6_2
        )
        
        # EBS CSI Driver for persistent volumes
        self.cluster.add_manifest("EbsCsiDriver", {
            "apiVersion": "v1",
            "kind": "StorageClass",
            "metadata": {
                "name": "gp3",
                "annotations": {
                    "storageclass.kubernetes.io/is-default-class": "true"
                }
            },
            "provisioner": "ebs.csi.aws.com",
            "volumeBindingMode": "WaitForFirstConsumer",
            "parameters": {
                "type": "gp3",
                "encrypted": "true"
            }
        })
        
        # Metrics Server for HPA
        self.cluster.add_helm_chart(
            "MetricsServer",
            chart="metrics-server",
            repository="https://kubernetes-sigs.github.io/metrics-server/",
            namespace="kube-system",
            values={
                "args": [
                    "--cert-dir=/tmp",
                    "--secure-port=4443",
                    "--kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname",
                    "--kubelet-use-node-status-port"
                ]
            }
        )
        
        # Cluster Autoscaler
        self._install_cluster_autoscaler()
    
    def _install_cluster_autoscaler(self) -> None:
        """Install cluster autoscaler for automatic node scaling"""
        
        # Create service account for cluster autoscaler
        cluster_autoscaler_sa = self.cluster.add_service_account(
            "ClusterAutoscalerServiceAccount",
            name="cluster-autoscaler",
            namespace="kube-system"
        )
        
        # Add permissions for cluster autoscaler
        cluster_autoscaler_sa.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:DescribeAutoScalingInstances",
                    "autoscaling:DescribeLaunchConfigurations",
                    "autoscaling:DescribeTags",
                    "autoscaling:SetDesiredCapacity",
                    "autoscaling:TerminateInstanceInAutoScalingGroup",
                    "ec2:DescribeLaunchTemplateVersions"
                ],
                resources=["*"]
            )
        )
        
        # Deploy cluster autoscaler
        self.cluster.add_manifest("ClusterAutoscaler", {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "cluster-autoscaler",
                "namespace": "kube-system",
                "labels": {
                    "app": "cluster-autoscaler"
                }
            },
            "spec": {
                "selector": {
                    "matchLabels": {
                        "app": "cluster-autoscaler"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "cluster-autoscaler"
                        }
                    },
                    "spec": {
                        "serviceAccountName": "cluster-autoscaler",
                        "containers": [
                            {
                                "image": "k8s.gcr.io/autoscaling/cluster-autoscaler:v1.21.0",
                                "name": "cluster-autoscaler",
                                "resources": {
                                    "limits": {
                                        "cpu": "100m",
                                        "memory": "300Mi"
                                    },
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "300Mi"
                                    }
                                },
                                "command": [
                                    "./cluster-autoscaler",
                                    "--v=4",
                                    "--stderrthreshold=info",
                                    "--cloud-provider=aws",
                                    "--skip-nodes-with-local-storage=false",
                                    "--expander=least-waste",
                                    f"--node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/{self.cluster.cluster_name}"
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "ssl-certs",
                                        "mountPath": "/etc/ssl/certs/ca-certificates.crt",
                                        "readOnly": True
                                    }
                                ],
                                "imagePullPolicy": "Always"
                            }
                        ],
                        "volumes": [
                            {
                                "name": "ssl-certs",
                                "hostPath": {
                                    "path": "/etc/ssl/certs/ca-bundle.crt"
                                }
                            }
                        ]
                    }
                }
            }
        })
    
    def _create_service_accounts(self) -> None:
        """Create service accounts with IRSA for AWS service access"""
        
        # Service account for Supabase GoTrue (needs SES access)
        self.gotrue_sa = self.cluster.add_service_account(
            "GoTrueServiceAccount",
            name="gotrue-sa",
            namespace="supabase"
        )
        
        # Add SES permissions for GoTrue
        self.gotrue_sa.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ses:SendEmail",
                    "ses:SendRawEmail",
                    "ses:GetSendQuota",
                    "ses:GetSendStatistics"
                ],
                resources=["*"]
            )
        )
        
        # Service account for Supabase Storage (needs S3 access)
        self.storage_sa = self.cluster.add_service_account(
            "StorageServiceAccount",
            name="storage-sa",
            namespace="supabase"
        )
        
        # Grant S3 permissions to storage service account
        self.managed_services.storage_bucket.grant_read_write(self.storage_sa)
        
        # Service account for accessing secrets
        self.secrets_sa = self.cluster.add_service_account(
            "SecretsServiceAccount",
            name="secrets-sa",
            namespace="supabase"
        )
        
        # Add Secrets Manager permissions
        self.secrets_sa.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[
                    self.managed_services.aurora_secret.secret_arn,
                    self.managed_services.docdb_secret.secret_arn,
                    self.managed_services.supabase_secret.secret_arn
                ]
            )
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for cluster information"""
        
        CfnOutput(
            self, "EksClusterName",
            value=self.cluster.cluster_name,
            description="EKS cluster name"
        )
        
        CfnOutput(
            self, "EksClusterEndpoint",
            value=self.cluster.cluster_endpoint,
            description="EKS cluster API endpoint"
        )
        
        CfnOutput(
            self, "EksClusterArn",
            value=self.cluster.cluster_arn,
            description="EKS cluster ARN"
        )
        
        CfnOutput(
            self, "KubectlConfig",
            value=f"aws eks update-kubeconfig --region {self.cluster.stack.region} --name {self.cluster.cluster_name}",
            description="kubectl configuration command"
        )
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """Return cluster information for use by other constructs"""
        return {
            "cluster": self.cluster,
            "cluster_name": self.cluster.cluster_name,
            "cluster_endpoint": self.cluster.cluster_endpoint,
            "service_accounts": {
                "gotrue": self.gotrue_sa,
                "storage": self.storage_sa,
                "secrets": self.secrets_sa
            }
        } 