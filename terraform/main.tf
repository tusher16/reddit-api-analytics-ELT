terraform {
    required_version = ">= 1.4.2" 

    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 4.16"
        }
    }
}

// Configure AWS provider
provider "aws" {
    region = var.aws_region // specify the AWS region to use
}

// Configure redshift cluster. 
resource "aws_redshift_cluster" "redshift" {
    cluster_identifier = "redshift-cluster-pipeline"                // specify the identifier for the Redshift cluster
    skip_final_snapshot = true                                      // set true so that Terraform can destroy the cluster without taking a final snapshot
    master_username    = "awsuser"                                  // specify the master username for the Redshift cluster
    master_password    = var.db_password                            // specify the master password for the Redshift cluster
    node_type          = "dc2.large"                                // specify the node type for the Redshift cluster
    cluster_type       = "single-node"                              // specify the cluster type for the Redshift cluster
    publicly_accessible = "true"                                    // set to true so that the Redshift cluster is publicly accessible
    iam_roles = [aws_iam_role.redshift_role.arn]                    // specify the IAM roles to associate with the Redshift cluster, which is set to the ARN of the IAM role created in the code
    vpc_security_group_ids = [aws_security_group.sg_redshift.id]    // specify the VPC security group IDs for the Redshift cluster, which is set to the ID of the security group created in the code
}

// Configure security group for Redshift allowing all inbound/outbound traffic
resource "aws_security_group" "sg_redshift" {
    name        = "sg_redshift" 
    ingress { 
        from_port       = 0
        to_port         = 0
        protocol        = "-1"
        cidr_blocks      = ["0.0.0.0/0"]
    }
    egress {
        from_port       = 0
        to_port         = 0
        protocol        = "-1"
        cidr_blocks      = ["0.0.0.0/0"]
    }
}

// Create IAM role with read-only access to S3. This role will be assigned to the Redshift cluster in order for it to read data from S3.
resource "aws_iam_role" "redshift_role" {
    name = "RedShiftLoadRole"                                                   // specify the name for the IAM role
    managed_policy_arns = ["arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"]    // specify the managed policy ARNs to associate with the IAM role
    assume_role_policy = jsonencode({                                           // specify the assume role policy document for the IAM role
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Sid    = ""
                Principal = {
                    Service = "redshift.amazonaws.com"
                }
            },
        ]
    })
}

// Create S3 bucket
resource "aws_s3_bucket" "reddit_bucket" {
    bucket = var.s3_bucket // specify the name for the S3 bucket
    force_destroy = true 
}

// Set access control of bucket to private
resource "aws_s3_bucket_acl" "s3_reddit_bucket_acl" {
  bucket = aws_s3_bucket.reddit_bucket.id
  acl    = "private"
}