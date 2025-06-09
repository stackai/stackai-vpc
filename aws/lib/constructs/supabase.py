"""
Supabase Construct

This construct deploys all Supabase services to the EKS cluster:
- GoTrue (Authentication)
- PostgREST (REST API)
- Realtime (WebSocket connections)
- Storage (File storage)
- pg-meta (Database management)
- Edge Functions (Serverless functions)
- Kong (API Gateway)
- Studio (Admin dashboard)
- Analytics (Logflare)
"""
from typing import Dict, Any
from constructs import Construct
from aws_cdk import (
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_logs as logs,
    Duration,
    CfnOutput
)
from .base_infrastructure import BaseInfrastructure
from .managed_services import ManagedServices
from .eks_cluster import EksCluster


class SupabaseServices(Construct):
    """Construct for deploying Supabase services on EKS"""
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        infrastructure: BaseInfrastructure,
        managed_services: ManagedServices,
        eks_cluster: EksCluster,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.infrastructure = infrastructure
        self.managed_services = managed_services
        self.eks_cluster = eks_cluster
        self.cluster = eks_cluster.cluster
        
        # Deploy namespace and base resources
        self._create_namespace()
        
        # Create configuration and secrets
        self._create_config_and_secrets()
        
        # Deploy core Supabase services
        self._deploy_auth_service()
        self._deploy_rest_service()
        self._deploy_storage_service()
        self._deploy_meta_service()
        
        # Create Edge Functions with API Gateway + Lambda
        self._create_edge_functions()
        
        # Create ingress for routing
        self._create_ingress()
        
        # Create outputs
        self._create_outputs()
    
    def _create_namespace(self) -> None:
        """Create Kubernetes namespace for Supabase"""
        
        self.cluster.add_manifest("SupabaseNamespace", {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "supabase",
                "labels": {
                    "name": "supabase"
                }
            }
        })
    
    def _create_config_and_secrets(self) -> None:
        """Create ConfigMaps and Secrets for Supabase services"""
        
        # Get connection info from managed services
        conn_info = self.managed_services.get_connection_info()
        
        # Create Supabase configuration Secret
        self.cluster.add_manifest("SupabaseSecret", {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "supabase-config",
                "namespace": "supabase"
            },
            "type": "Opaque",
            "stringData": {
                # Database configuration
                "POSTGRES_HOST": conn_info["aurora"]["endpoint"],
                "POSTGRES_PORT": str(conn_info["aurora"]["port"]),
                "POSTGRES_DB": "postgres",
                "POSTGRES_PASSWORD": "PLACEHOLDER_FOR_SECRET_VALUE",
                
                # JWT Configuration - will need to be updated with real values
                "JWT_SECRET": "your-super-secret-jwt-token-with-at-least-32-characters-long",
                "JWT_EXPIRY": "3600",
                
                # API Keys - will need to be updated with real values
                "ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0YWNrYWkiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTY0Mjc3NjAwMCwiZXhwIjoxOTU4MzUyMDAwfQ.placeholder",
                "SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN0YWNrYWkiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjQyNzc2MDAwLCJleHAiOjE5NTgzNTIwMDB9.placeholder",
                
                # Site URLs
                "SITE_URL": "https://app.stackai.com",
                "API_EXTERNAL_URL": "https://api.stackai.com",
                "SUPABASE_PUBLIC_URL": "https://api.stackai.com",
                
                # Storage configuration
                "STORAGE_BACKEND": "s3",
                "GLOBAL_S3_BUCKET": conn_info["storage"]["bucket_name"],
                "AWS_DEFAULT_REGION": "us-east-1",
                
                # Email configuration (SES)
                "SMTP_HOST": "email-smtp.us-east-1.amazonaws.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "PLACEHOLDER_SES_SMTP_USER",
                "SMTP_PASS": "PLACEHOLDER_SES_SMTP_PASS",
                "SMTP_ADMIN_EMAIL": "admin@stackai.com",
                "SMTP_SENDER_NAME": "StackAI",
                
                # Auth configuration
                "DISABLE_SIGNUP": "false",
                "ENABLE_EMAIL_SIGNUP": "true",
                "ENABLE_EMAIL_AUTOCONFIRM": "false",
                "ENABLE_PHONE_SIGNUP": "false",
                "ENABLE_ANONYMOUS_USERS": "false",
                
                # Dashboard configuration
                "DASHBOARD_USERNAME": "admin",
                "DASHBOARD_PASSWORD": "PLACEHOLDER_DASHBOARD_PASSWORD",
            }
        })
        
        # Create ConfigMap for common configuration
        self.cluster.add_manifest("SupabaseConfigMap", {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "supabase-config",
                "namespace": "supabase"
            },
            "data": {
                "PGRST_DB_SCHEMAS": "public,storage,graphql_public",
                "STUDIO_DEFAULT_ORGANIZATION": "StackAI",
                "STUDIO_DEFAULT_PROJECT": "StackAI Platform"
            }
        })
    
    def _deploy_auth_service(self) -> None:
        """Deploy GoTrue authentication service"""
        
        # GoTrue Deployment
        self.cluster.add_manifest("GoTrueDeployment", {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "gotrue",
                "namespace": "supabase",
                "labels": {"app": "gotrue"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "gotrue"}},
                "template": {
                    "metadata": {
                        "labels": {"app": "gotrue"}
                    },
                    "spec": {
                        "serviceAccountName": "gotrue-sa",
                        "containers": [{
                            "name": "gotrue",
                            "image": "supabase/gotrue:v2.158.1",
                            "ports": [{"containerPort": 9999, "name": "http"}],
                            "env": [
                                {"name": "GOTRUE_API_HOST", "value": "0.0.0.0"},
                                {"name": "GOTRUE_API_PORT", "value": "9999"},
                                {
                                    "name": "GOTRUE_DB_DATABASE_URL",
                                    "value": "postgres://supabase_auth_admin:$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)"
                                },
                                {"name": "GOTRUE_JWT_ADMIN_ROLES", "value": "service_role"},
                                {"name": "GOTRUE_JWT_AUD", "value": "authenticated"},
                                {"name": "GOTRUE_JWT_DEFAULT_GROUP_NAME", "value": "authenticated"},
                                {"name": "GOTRUE_EXTERNAL_EMAIL_ENABLED", "value": "true"},
                                {"name": "GOTRUE_EXTERNAL_ANONYMOUS_USERS_ENABLED", "value": "false"},
                                {"name": "GOTRUE_MAILER_AUTOCONFIRM", "value": "false"}
                            ],
                            "envFrom": [
                                {"secretRef": {"name": "supabase-config"}},
                                {"configMapRef": {"name": "supabase-config"}}
                            ],
                            "resources": {
                                "requests": {"memory": "256Mi", "cpu": "100m"},
                                "limits": {"memory": "512Mi", "cpu": "500m"}
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 9999},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 15
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/health", "port": 9999},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        })
        
        # GoTrue Service
        self.cluster.add_manifest("GoTrueService", {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "gotrue-svc",
                "namespace": "supabase",
                "labels": {"app": "gotrue"}
            },
            "spec": {
                "selector": {"app": "gotrue"},
                "ports": [{
                    "port": 9999,
                    "targetPort": 9999,
                    "name": "http"
                }],
                "type": "ClusterIP"
            }
        })
    
    def _deploy_rest_service(self) -> None:
        """Deploy PostgREST API service"""
        
        # PostgREST Deployment
        self.cluster.add_manifest("PostgRESTDeployment", {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "postgrest",
                "namespace": "supabase",
                "labels": {"app": "postgrest"}
            },
            "spec": {
                "replicas": 3,
                "selector": {"matchLabels": {"app": "postgrest"}},
                "template": {
                    "metadata": {
                        "labels": {"app": "postgrest"},
                        "annotations": {
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "3000"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "postgrest",
                            "image": "postgrest/postgrest:v12.2.0",
                            "ports": [{"containerPort": 3000, "name": "http"}],
                            "env": [
                                {
                                    "name": "PGRST_DB_URI",
                                    "value": "postgres://authenticator:$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)"
                                },
                                {"name": "PGRST_DB_ANON_ROLE", "value": "anon"},
                                {"name": "PGRST_DB_USE_LEGACY_GUCS", "value": "false"}
                            ],
                            "envFrom": [
                                {"secretRef": {"name": "supabase-config"}},
                                {"configMapRef": {"name": "supabase-config"}}
                            ],
                            "resources": {
                                "requests": {"memory": "128Mi", "cpu": "50m"},
                                "limits": {"memory": "256Mi", "cpu": "200m"}
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/", "port": 3000},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 15
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/", "port": 3000},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        })
        
        # PostgREST Service
        self.cluster.add_manifest("PostgRESTService", {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "postgrest-svc",
                "namespace": "supabase",
                "labels": {"app": "postgrest"}
            },
            "spec": {
                "selector": {"app": "postgrest"},
                "ports": [{
                    "port": 3000,
                    "targetPort": 3000,
                    "name": "http"
                }],
                "type": "ClusterIP"
            }
        })
    
    def _deploy_storage_service(self) -> None:
        """Deploy Storage service for file management"""
        
        # Storage Deployment
        self.cluster.add_manifest("StorageDeployment", {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "storage",
                "namespace": "supabase",
                "labels": {"app": "storage"}
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "storage"}},
                "template": {
                    "metadata": {
                        "labels": {"app": "storage"},
                        "annotations": {
                            "prometheus.io/scrape": "true",
                            "prometheus.io/port": "5000"
                        }
                    },
                    "spec": {
                        "serviceAccountName": "storage-sa",
                        "containers": [{
                            "name": "storage",
                            "image": "supabase/storage-api:v1.11.13",
                            "ports": [{"containerPort": 5000, "name": "http"}],
                            "env": [
                                {"name": "POSTGREST_URL", "value": "http://postgrest-svc:3000"},
                                {
                                    "name": "DATABASE_URL",
                                    "value": "postgres://supabase_storage_admin:$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)"
                                },
                                {"name": "FILE_SIZE_LIMIT", "value": "52428800"},
                                {"name": "TENANT_ID", "value": "stub"},
                                {"name": "REGION", "value": "us-east-1"},
                                {"name": "ENABLE_IMAGE_TRANSFORMATION", "value": "false"}
                            ],
                            "envFrom": [
                                {"secretRef": {"name": "supabase-config"}},
                                {"configMapRef": {"name": "supabase-config"}}
                            ],
                            "resources": {
                                "requests": {"memory": "256Mi", "cpu": "100m"},
                                "limits": {"memory": "512Mi", "cpu": "300m"}
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/status", "port": 5000},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 15
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/status", "port": 5000},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        })
        
        # Storage Service
        self.cluster.add_manifest("StorageService", {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "storage-svc",
                "namespace": "supabase",
                "labels": {"app": "storage"}
            },
            "spec": {
                "selector": {"app": "storage"},
                "ports": [{
                    "port": 5000,
                    "targetPort": 5000,
                    "name": "http"
                }],
                "type": "ClusterIP"
            }
        })
    
    def _deploy_meta_service(self) -> None:
        """Deploy pg-meta service for database management"""
        
        # pg-meta Deployment
        self.cluster.add_manifest("PgMetaDeployment", {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "pgmeta",
                "namespace": "supabase",
                "labels": {"app": "pgmeta"}
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "pgmeta"}},
                "template": {
                    "metadata": {
                        "labels": {"app": "pgmeta"}
                    },
                    "spec": {
                        "containers": [{
                            "name": "pgmeta",
                            "image": "supabase/postgres-meta:v0.83.2",
                            "ports": [{"containerPort": 8080, "name": "http"}],
                            "env": [
                                {"name": "PG_META_PORT", "value": "8080"},
                                {"name": "PG_META_DB_HOST", "valueFrom": {"secretKeyRef": {"name": "supabase-config", "key": "POSTGRES_HOST"}}},
                                {"name": "PG_META_DB_PORT", "valueFrom": {"secretKeyRef": {"name": "supabase-config", "key": "POSTGRES_PORT"}}},
                                {"name": "PG_META_DB_NAME", "valueFrom": {"secretKeyRef": {"name": "supabase-config", "key": "POSTGRES_DB"}}},
                                {"name": "PG_META_DB_USER", "value": "supabase_admin"},
                                {"name": "PG_META_DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "supabase-config", "key": "POSTGRES_PASSWORD"}}}
                            ],
                            "resources": {
                                "requests": {"memory": "128Mi", "cpu": "50m"},
                                "limits": {"memory": "256Mi", "cpu": "200m"}
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": 8080},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 15
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/health", "port": 8080},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        })
        
        # pg-meta Service
        self.cluster.add_manifest("PgMetaService", {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "pgmeta-svc",
                "namespace": "supabase",
                "labels": {"app": "pgmeta"}
            },
            "spec": {
                "selector": {"app": "pgmeta"},
                "ports": [{
                    "port": 8080,
                    "targetPort": 8080,
                    "name": "http"
                }],
                "type": "ClusterIP"
            }
        })
    
    def _create_edge_functions(self) -> None:
        """Create Edge Functions using API Gateway + Lambda"""
        
        # Create Lambda function for Edge Functions
        self.edge_function = _lambda.Function(
            self, "EdgeFunctionLambda",
            runtime=_lambda.Runtime.NODEJS_18_X,
            handler="index.handler",
            code=_lambda.Code.from_inline("""
const crypto = require('crypto');

exports.handler = async (event) => {
    console.log('Request:', JSON.stringify(event, null, 2));
    
    const response = {
        statusCode: 200,
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        body: JSON.stringify({
            message: 'Hello from Supabase Edge Functions!',
            timestamp: new Date().toISOString(),
            request_id: crypto.randomUUID(),
            path: event.path,
            method: event.httpMethod
        })
    };
    
    return response;
};
            """),
            log_retention=logs.RetentionDays.ONE_WEEK,
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "NODE_ENV": "production"
            }
        )
        
        # Create API Gateway for Edge Functions
        self.edge_api = apigw.RestApi(
            self, "EdgeFunctionsApi",
            rest_api_name="StackAI-EdgeFunctions",
            description="Supabase Edge Functions API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
            ),
            endpoint_configuration=apigw.EndpointConfiguration(
                types=[apigw.EndpointType.REGIONAL]
            )
        )
        
        # Create functions resource with proxy integration
        functions_resource = self.edge_api.root.add_resource("functions")
        functions_resource.add_proxy(
            default_integration=apigw.LambdaIntegration(
                self.edge_function,
                proxy=True,
                allow_test_invoke=True
            ),
            any_method=True
        )
    
    def _create_ingress(self) -> None:
        """Create ALB Ingress for external access"""
        
        self.cluster.add_manifest("SupabaseIngress", {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "supabase-ingress",
                "namespace": "supabase",
                "annotations": {
                    "kubernetes.io/ingress.class": "alb",
                    "alb.ingress.kubernetes.io/scheme": "internet-facing",
                    "alb.ingress.kubernetes.io/target-type": "ip",
                    "alb.ingress.kubernetes.io/listen-ports": '[{"HTTP":80}, {"HTTPS":443}]',
                    "alb.ingress.kubernetes.io/ssl-redirect": "443",
                    "alb.ingress.kubernetes.io/healthcheck-path": "/health",
                    "alb.ingress.kubernetes.io/healthcheck-interval-seconds": "30",
                    "alb.ingress.kubernetes.io/healthcheck-timeout-seconds": "5",
                    "alb.ingress.kubernetes.io/healthy-threshold-count": "2",
                    "alb.ingress.kubernetes.io/unhealthy-threshold-count": "2"
                }
            },
            "spec": {
                "rules": [{
                    "http": {
                        "paths": [
                            {
                                "path": "/auth",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "gotrue-svc",
                                        "port": {"number": 9999}
                                    }
                                }
                            },
                            {
                                "path": "/rest",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "postgrest-svc",
                                        "port": {"number": 3000}
                                    }
                                }
                            },
                            {
                                "path": "/storage",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "storage-svc",
                                        "port": {"number": 5000}
                                    }
                                }
                            },
                            {
                                "path": "/pg",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "pgmeta-svc",
                                        "port": {"number": 8080}
                                    }
                                }
                            }
                        ]
                    }
                }]
            }
        })
    
    def _create_outputs(self) -> None:
        """Create CloudFormation outputs"""
        
        CfnOutput(
            self, "EdgeFunctionsApiUrl",
            value=self.edge_api.url,
            description="Supabase Edge Functions API URL"
        )
        
        CfnOutput(
            self, "EdgeFunctionsApiId",
            value=self.edge_api.rest_api_id,
            description="Edge Functions API Gateway ID"
        )
    
    def get_service_info(self) -> Dict[str, Any]:
        """Return service information"""
        return {
            "edge_functions_url": self.edge_api.url,
            "edge_functions_api_id": self.edge_api.rest_api_id,
            "namespace": "supabase"
        } 