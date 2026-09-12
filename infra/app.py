"""Minimal CDK app documenting the RentaLista stack (optional full deploy).

Runtime/Gateway/Browser were created via CLI for the hackathon demo.
This stack captures the durable web + API pieces for destroy/recreate.
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from constructs import Construct


class RentaListaWebStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "WebBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        dist = cloudfront.Distribution(
            self,
            "WebDist",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(10),
                )
            ],
        )

        s3deploy.BucketDeployment(
            self,
            "DeployWeb",
            sources=[s3deploy.Source.asset("../frontend/out")],
            destination_bucket=bucket,
            distribution=dist,
            distribution_paths=["/*"],
        )

        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "DistributionDomain", value=dist.distribution_domain_name)


app = cdk.App()
RentaListaWebStack(app, "RentaListaWeb")
app.synth()
