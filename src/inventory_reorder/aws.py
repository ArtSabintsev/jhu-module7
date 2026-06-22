from __future__ import annotations

import boto3

from inventory_reorder.settings import Settings


class AwsClients:
    def __init__(self, settings: Settings) -> None:
        self.session = boto3.Session(region_name=settings.aws_region)
        self.sns = self.session.client("sns")
        self.sqs = self.session.client("sqs")
        self.dynamodb = self.session.resource("dynamodb")
