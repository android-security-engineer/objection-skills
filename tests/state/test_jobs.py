import unittest
from unittest import mock

from objection.state.jobs import job_manager_state, Job


class TestJobManager(unittest.TestCase):
    def tearDown(self):
        job_manager_state.jobs = {}

    def test_job_manager_starts_with_empty_jobs(self):
        self.assertEqual(len(job_manager_state.jobs), 0)

    def test_adds_jobs(self):
        job_manager_state.jobs = {}
        job = Job('foo', 'hook', None, 100001)
        job_manager_state.add_job(job)

        self.assertEqual(len(job_manager_state.jobs), 1)

    def test_removes_jobs(self):
        job1 = Job('foo', 'script', None)
        job2 = Job('bar', 'script', None)
        job_manager_state.add_job(job1)
        job_manager_state.add_job(job2)

        job_manager_state.remove_job(job1.uuid)
        job_manager_state.remove_job(job2.uuid)
        self.assertEqual(len(job_manager_state.jobs), 0)

    @mock.patch('objection.state.jobs.state_connection.get_api')
    def test_removes_hook_jobs(self, mock_api):
        job_manager_state.jobs = {}
        j1 = Job('foo', 'hook', None, 100002)
        j2 = Job('bar', 'hook', None, 100003)
        job_manager_state.add_job(j1)
        job_manager_state.add_job(j2)

        job_manager_state.remove_job(j1.uuid)
        job_manager_state.remove_job(j2.uuid)
        self.assertEqual(len(job_manager_state.jobs), 0)
