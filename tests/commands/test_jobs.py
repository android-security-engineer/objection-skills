import unittest
from unittest import mock

from objection.commands.jobs import show, kill
from objection.state.jobs import job_manager_state, Job
from ..helpers import capture


class MockJob:
    """
        A mock job for testing purposes
    """

    def __init__(self):
        self.id = '3c3c65c7-67d2-4617-8fba-b96b6d2130d7'
        self.started = '2017-10-14 09:21:01'
        self.name = 'test'
        self.args = ['--foo', 'bar']

    def end(self):
        pass


class TestJobs(unittest.TestCase):
    def setUp(self):
        self.mock_job = MockJob()

    def tearDown(self):
        job_manager_state.jobs = {}

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_displays_empty_jobs_message(self, mock_api):
        mock_api.return_value.jobs_get.return_value = []
        with capture(show) as o:
            output = o

        # 不锁定 tabulate 精确列宽，断言表头
        for token in ('Job ID', 'Type', 'Name'):
            self.assertIn(token, output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_displays_list_of_jobs(self, mock_api):
        mock_api.return_value.jobs_get.return_value = [
            {'identifier': '123456', 'invocations': [{}], 'type': 'ios-jailbreak-disable'}]

        with capture(show, []) as o:
            output = o

        for token in ('Job ID', 'Type', 'Name', 'ios-jailbreak-disable'):
            self.assertIn(token, output)

    def test_kill_validates_arguments(self):
        with capture(kill, []) as o:
            output = o

        self.assertEqual(output, 'Usage: jobs kill <uuid>\n')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_cant_find_job_by_uuid(self, mock_api):
        # 不存在的 uuid 不应抛异常，也不应调用 jobs_kill（job 不在本地状态）
        kill(['nonexistent-uuid'])

        self.assertFalse(mock_api.return_value.jobs_kill.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_kills_job_by_uuid(self, mock_api):
        # 预置一个 job，再 kill 它，验证 jobs_kill 被调用
        from objection.state.jobs import Job
        job_manager_state.jobs = {}
        job = Job('test', 'hook', mock.MagicMock(), 12345)
        job_manager_state.jobs[12345] = job

        kill(['12345'])

        self.assertTrue(mock_api.return_value.jobs_kill.called)
        self.assertNotIn(12345, job_manager_state.jobs)
