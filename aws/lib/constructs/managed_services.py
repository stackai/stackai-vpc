"""
Managed Services Construct

This construct creates and configures AWS managed services:
- Aurora Serverless v2 (PostgreSQL) for Supabase
- DocumentDB for MongoDB workloads
- ElastiCache Redis for Celery and caching
- S3 bucket for Supabase Storage
- Secrets Manager for credentials
"""
from typing import Dict, Any
from constructs import Construct
from aws_cdk import (
    aws_rds as rds,
    aws_docdb as docdb,
    aws_elasticache as elasticache,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from .base_infrastructure import BaseInfrastructure


class ManagedServices(Construct):
    """Construct for AWS managed services used by StackAI"""
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str, 
        infrastructure: BaseInfrastructure,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.infrastructure = infrastructure
        
        # Create secrets first
        self._create_secrets()
        
        # Create Aurora PostgreSQL cluster
        self._create_aurora_cluster()
        
        # Create DocumentDB cluster
        self._create_documentdb_cluster()
        
        # Create ElastiCache Redis
        self._create_redis_cluster()
        
        # Create S3 bucket for storage
        self._create_s3_bucket()
        
        # Output service endpoints
        self._create_outputs()
    
    def _create_secrets(self) -> None:
        """Create secrets for database credentials"""
        
        # DocumentDB admin secret
        self.docdb_secret = secretsmanager.Secret(
            self, "DocDbAdminSecret",
            secret_name="stackai-docdb-admin",
            description="DocumentDB administrator credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"docdb_admin"}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=32,
                exclude_characters='"@/\\'
            )
        )
        
        # Supabase database secrets
        self.supabase_secret = secretsmanager.Secret(
            self, "SupabaseSecret",
            secret_name="stackai-supabase",
            description="Supabase application secrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"jwt_secret":"","anon_key":"","service_role_key":""}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=64
            )
        )
    
    def _create_aurora_cluster(self) -> None:
        """Create Aurora Serverless v2 PostgreSQL cluster"""
        
        # Create DB subnet group
        db_subnet_group = rds.SubnetGroup(
            self, "AuroraSubnetGroup",
            description="Subnet group for Aurora PostgreSQL",
            vpc=self.infrastructure.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )
        
        # Create parameter group for PostgreSQL optimization
        parameter_group = rds.ParameterGroup(
            self, "AuroraParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            description="Parameter group for StackAI Aurora PostgreSQL",
            parameters={
                "shared_preload_libraries": "pg_stat_statements,pg_hint_plan",
                "log_statement": "all",
                "log_min_duration_statement": "1000",
                "track_activity_query_size": "2048"
            }
        )
        
        # Create Aurora Serverless v2 cluster
        self.aurora_cluster = rds.DatabaseCluster(
            self, "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_4
            ),
            credentials=rds.Credentials.from_generated_secret(
                username="postgres",
                secret_name="stackai-aurora-postgres"
            ),
            vpc=self.infrastructure.vpc,
            subnet_group=db_subnet_group,
            security_groups=[self.infrastructure.rds_sg],
            default_database_name="postgres",
            parameter_group=parameter_group,
            backup=rds.BackupProps(
                retention=Duration.days(7),
                preferred_window="03:00-04:00"
            ),
            preferred_maintenance_window="sun:04:00-sun:05:00",
            cloudwatch_logs_exports=["postgresql"],
            removal_policy=RemovalPolicy.DESTROY,  # Change to RETAIN for production
            writer=rds.ClusterInstance.serverless_v2(
                "writer",
                auto_minor_version_upgrade=True
            ),
            readers=[
                rds.ClusterInstance.serverless_v2(
                    "reader",
                    scale_with_writer=True,
                    auto_minor_version_upgrade=True
                )
            ],
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=16
        )
    
    def _create_documentdb_cluster(self) -> None:
        """Create DocumentDB cluster for MongoDB workloads"""
        
        # Create DocumentDB subnet group
        docdb_subnet_group = docdb.CfnDBSubnetGroup(
            self, "DocDbSubnetGroup",
            db_subnet_group_description="Subnet group for DocumentDB",
            subnet_ids=[subnet.subnet_id for subnet in self.infrastructure.private_subnets],
            db_subnet_group_name="stackai-docdb-subnet-group"
        )
        
        # Create DocumentDB cluster
        self.docdb_cluster = docdb.CfnDBCluster(
            self, "DocDbCluster",
            master_username=self.docdb_secret.secret_value_from_json("username").unsafe_unwrap(),
            master_user_password=self.docdb_secret.secret_value_from_json("password").unsafe_unwrap(),
            db_subnet_group_name=docdb_subnet_group.ref,  # Use ref instead of db_subnet_group_name
            vpc_security_group_ids=[self.infrastructure.docdb_sg.security_group_id],
            backup_retention_period=7,
            preferred_backup_window="03:00-04:00",
            preferred_maintenance_window="sun:04:00-sun:05:00",
            storage_encrypted=True,
            deletion_protection=False  # Set to True for production
        )
        
        # Add dependency - cluster depends on subnet group
        self.docdb_cluster.add_dependency(docdb_subnet_group)
        
        # Create DocumentDB instances
        for i in range(2):  # Primary + 1 replica for HA
            docdb_instance = docdb.CfnDBInstance(
                self, f"DocDbInstance{i+1}",
                db_cluster_identifier=self.docdb_cluster.ref,
                db_instance_class="db.t3.medium",
                auto_minor_version_upgrade=True
            )
            # Instance depends on cluster
            docdb_instance.add_dependency(self.docdb_cluster)
    
    def _create_redis_cluster(self) -> None:
        """Create ElastiCache Redis cluster"""
        
        # Create Redis subnet group
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self, "RedisSubnetGroup",
            description="Subnet group for Redis",
            subnet_ids=[subnet.subnet_id for subnet in self.infrastructure.private_subnets],
            cache_subnet_group_name="stackai-redis-subnet-group"
        )
        
        # Create Redis parameter group
        redis_parameter_group = elasticache.CfnParameterGroup(
            self, "RedisParameterGroup",
            cache_parameter_group_family="redis7",
            description="Parameter group for StackAI Redis",
            properties={
                "maxmemory-policy": "allkeys-lru",
                "timeout": "300",
                "tcp-keepalive": "300"
            }
        )
        
        # Create Redis replication group for HA
        self.redis_cluster = elasticache.CfnReplicationGroup(
            self, "RedisCluster",
            replication_group_description="Redis cluster for StackAI caching and Celery",
            cache_node_type="cache.t3.micro",
            engine="redis",
            engine_version="7.0",
            num_cache_clusters=2,  # Primary + 1 replica
            automatic_failover_enabled=True,
            multi_az_enabled=True,
            cache_subnet_group_name=redis_subnet_group.ref,  # Use ref instead of cache_subnet_group_name
            cache_parameter_group_name=redis_parameter_group.ref,
            security_group_ids=[self.infrastructure.redis_sg.security_group_id],
            at_rest_encryption_enabled=True,
            transit_encryption_enabled=True,
            preferred_maintenance_window="sun:04:00-sun:05:00",
            snapshot_retention_limit=5,
            snapshot_window="03:00-04:00"
        )
        
        # Add dependencies
        self.redis_cluster.add_dependency(redis_subnet_group)
        self.redis_cluster.add_dependency(redis_parameter_group)
    
    def _create_s3_bucket(self) -> None:
        """Create S3 bucket for Supabase Storage"""
        
        self.storage_bucket = s3.Bucket(
            self, "SupabaseStorageBucket",
            bucket_name=None,  # Let CDK generate unique name
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,  # Change to RETAIN for production
            auto_delete_objects=True,  # Change to False for production
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipartUploads",
                    abort_incomplete_multipart_upload_after=Duration.days(1)
                ),
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD
                    ],
                    allowed_origins=["*"],  # Restrict this in production
                    max_age=3000
                )
            ]
        )
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs for service endpoints"""
        
        CfnOutput(
            self, "AuroraClusterEndpoint",
            value=self.aurora_cluster.cluster_endpoint.hostname,
            description="Aurora PostgreSQL cluster endpoint"
        )
        
        CfnOutput(
            self, "AuroraClusterReaderEndpoint", 
            value=self.aurora_cluster.cluster_read_endpoint.hostname,
            description="Aurora PostgreSQL cluster reader endpoint"
        )
        
        CfnOutput(
            self, "DocumentDbEndpoint",
            value=self.docdb_cluster.attr_endpoint,
            description="DocumentDB cluster endpoint"
        )
        
        CfnOutput(
            self, "RedisEndpoint",
            value=self.redis_cluster.attr_configuration_end_point_address,
            description="Redis cluster configuration endpoint"
        )
        
        CfnOutput(
            self, "StorageBucketName",
            value=self.storage_bucket.bucket_name,
            description="S3 bucket name for Supabase Storage"
        )
        
        CfnOutput(
            self, "DocDbSecretArn",
            value=self.docdb_secret.secret_arn,
            description="DocumentDB credentials secret ARN"
        )
        
        CfnOutput(
            self, "SupabaseSecretArn",
            value=self.supabase_secret.secret_arn,
            description="Supabase application secrets ARN"
        )
    
    @property
    def aurora_secret(self) -> secretsmanager.ISecret:
        """Return Aurora cluster secret"""
        return self.aurora_cluster.secret
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Return connection information for all services"""
        return {
            "aurora": {
                "endpoint": self.aurora_cluster.cluster_endpoint.hostname,
                "port": self.aurora_cluster.cluster_endpoint.port,
                "secret_arn": self.aurora_cluster.secret.secret_arn
            },
            "documentdb": {
                "endpoint": self.docdb_cluster.attr_endpoint,
                "port": 27017,
                "secret_arn": self.docdb_secret.secret_arn
            },
            "redis": {
                "endpoint": self.redis_cluster.attr_configuration_end_point_address,
                "port": 6379
            },
            "storage": {
                "bucket_name": self.storage_bucket.bucket_name
            }
        } 