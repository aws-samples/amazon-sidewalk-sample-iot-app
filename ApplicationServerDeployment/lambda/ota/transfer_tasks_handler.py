# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from typing import List

import boto3
import logging

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from task import TransferTask

logger = logging.getLogger(__name__)


class TransferTasksHandler:
    """
    A class that provides read and write methods for the TransferTasks table.
    """

    TABLE_NAME = 'TransferTasks'
    PRIMARY_KEY = 'task_id'    
    def __init__(self):
        self._table = boto3.resource('dynamodb').Table(self.TABLE_NAME)

    # ----------------
    # Read operations
    # ----------------

    def get_all_transfer_tasks(self) -> List[TransferTask]:
        """
        Gets all available records from the TransferTasks table.

        :return:    List of TransferTasks objects.
        """
        try:
            response = self._table.scan()
            items = response.get('Items', [])

            for item in items:
                yield TransferTask(**item)

            while "LastEvaluatedKey" in response:
                response = self._table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
                items = response.get('Items', [])

                for item in items:
                    yield TransferTask(**item)

        except ClientError as err:
            logger.error(f'Error while calling get_all_transfer_tasks: {err}', exc_info=True)
            raise

    def get_transfer_task_details(self, task_id: str) -> TransferTask:
        """
        Queries Measurements table for the records coming from given device withing a given time span.

        :param task id:  taskId
        :return:                    task Detail
        """
        items = []
        try:
            response = self._table.query(KeyConditionExpression=Key('task_id').eq(task_id))
            items = response.get('Items', [])
        except ClientError as err:
            logger.error(f'Error while calling get_transfer_task_details: {err}')
            raise
        else:
            return TransferTask(**items[0])


    # -----------------
    # Write operations
    # -----------------
    def add_transfer_task(self, transferTask: TransferTask):
        """
        Adds transferTask object to the TransferTasks table.

        :param taskId:  Task identifier.
        :return:             Updated TransferTask object.
        """
        try:
            self._table.put_item(
                Item={
                    'task_id': transferTask.get_task_id(),
                    'task_status': transferTask.get_task_status(),
                    'creation_time_UTC': transferTask.get_creation_time_UTC(),
                    'task_start_time_UTC': transferTask.get_task_start_time_UTC(),
                    'task_end_time_UTC': transferTask.get_task_end_time_UTC(),
                    'file_name': transferTask.get_file_name(),
                    'file_size_kb': transferTask.get_file_size_kb(),
                    'origination': transferTask.get_origination(),
                    'device_ids': transferTask.get_device_ids()
                },
                ReturnValues="ALL_OLD"
            )
        except ClientError as err:
            logger.error(
                f'Error while calling add_transfer_task for task_id: {transferTask.get_task_id()}: {err}'
            )
            raise
        else:
            return transferTask


    def update_transfer_task_start_details(self, transfer_task: TransferTask):
        """
        Updates deviceTransfer object in the DeviceTransfers table.

        param deviceTransfer: Updated DeviceTransfer object.
        """
        try:
            self._table.update_item(
                Key={
                    'task_id': transfer_task.get_task_id()
                },
                UpdateExpression="SET task_status = :status ,"
                                 "task_start_time_UTC = :start_time ",
                ExpressionAttributeValues={
                    ':status': transfer_task.get_transfer_status(),
                    ':start_time': transfer_task.get_task_start_time_UTC(),
                    ':end_time': transfer_task.get_task_end_time_UTC()
                },
                ReturnValues="ALL_NEW"  # You can adjust the return values as needed
            )
        except Exception as e:
            # Handle the exception according to your requirements
            print(f"Error updating item: {e}")

    def update_transfer_task_finish_details(self, transfer_task: TransferTask):
        """
        Updates deviceTransfer object in the DeviceTransfers table.

        param deviceTransfer: Updated DeviceTransfer object.
        """
        try:
            self._table.update_item(
                Key={
                    'task_id': transfer_task.get_task_id()
                },
                UpdateExpression="SET transfer_status = :status, "
                                 "task_end_time_UTC = :end_time ",
                ExpressionAttributeValues={
                    ':status': transfer_task.get_transfer_status(),
                    ':end_time': transfer_task.get_task_end_time_UTC()
                },
                ReturnValues="ALL_NEW"  # You can adjust the return values as needed
            )
        except Exception as e:
            # Handle the exception according to your requirements
            print(f"Error updating item: {e}")
   
    # -----------------
    # Update operations
    # -----------------
    def update_transfer_task(self, transfer_task: TransferTask):
        """
        Updates transfer_task object to the TransferTasks table.

        :param transfer_task:   Task.
        :return:                Updated TransferTask object.
        """
        try:
            self._table.put_item(Item=transfer_task.to_dict())
        except ClientError as err:
            logger.error(
                f'Error while calling update_transfer_task for task_id: {transfer_task.get_task_id()}: {err}'
            )
            raise
        else:
            return transfer_task
