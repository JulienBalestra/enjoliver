"""
POC for prometheus client
"""
from prometheus_client import multiprocess


def worker_exit(server, worker):
    """
    :param server:
    :param worker:
    :return:
    """
    multiprocess.mark_process_dead(worker.pid)
