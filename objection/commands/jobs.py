import uuid
from tabulate import tabulate
from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result
from ..state.jobs import job_manager_state, Job


def show(args: list = None) -> CommandResult:
    """
        Show all of the jobs that are currently running

        :return:
    """

    sync_job_manager()
    jobs = job_manager_state.jobs

    human_lines = tabulate(
        [[
            uuid,
            job.job_type,
            job.name,
        ] for uuid, job in jobs.items()], headers=['Job ID', 'Type', 'Name'],
    )
    return output_result(
        CommandResult(
            result={
                'jobs': [
                    {'id': uuid, 'type': job.job_type, 'name': job.name}
                    for uuid, job in jobs.items()
                ],
                'count': len(jobs),
            },
            human_text=human_lines,
        ),
        command='jobs list',
    )


def kill(args: list) -> CommandResult:
    """
        Kills a specific objection job.

        :param args:
        :return:
    """

    if len(args) <= 0:
        human_text = 'Usage: jobs kill <uuid>'
        return output_result(
            CommandResult(
                result={'error': 'missing job uuid'},
                status='error',
                human_text=human_text,
            ),
            command='jobs kill',
        )

    # agent 返回的 job identifier 通常是 base36 字符串（如 rdcjq16g8xi），
    # 也可能是纯数字。尽量转 int 以兼容旧逻辑，失败则原样保留为字符串。
    raw = args[0]
    try:
        job_uuid = int(raw)
    except ValueError:
        job_uuid = raw

    job_manager_state.remove_job(job_uuid)

    return output_result(
        CommandResult(result={'killed': job_uuid}, human_text='Job {0} killed'.format(job_uuid)),
        command='jobs kill',
    )


def list_current_jobs() -> dict:
    """
        Return a list of the currently listed objection jobs.
        Used for tab completion in the repl.
    """

    sync_job_manager()
    resp = {}

    for uuid, job in job_manager_state.jobs.items():
        resp[str(uuid)] = str(uuid)

    return resp


def sync_job_manager() -> dict[int, Job]:
    try:
        api = state_connection.get_api()
        jobs = api.jobs_get()

        # 若状态被外部置为 list（兼容旧测试/调用方），重置为 dict
        if not isinstance(job_manager_state.jobs, dict):
            job_manager_state.jobs = {}

        for job in jobs:
            # identifier 通常是 base36 字符串（如 rdcjq16g8xi），也可能是纯数字
            raw_id = job['identifier']
            try:
                job_uuid = int(raw_id)
            except (ValueError, TypeError):
                job_uuid = raw_id
            job_name = job['type']
            if job_uuid not in job_manager_state.jobs:
                job_manager_state.jobs[job_uuid] = Job(job_name, 'hook', None, job_uuid)

        return job_manager_state.jobs
    except Exception:
        pass

