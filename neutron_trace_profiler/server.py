import GreenletProfiler
import logging
import os
import webob.dec
import webob.exc

from neutron.agent.linux import utils as agent_utils
from oslo_config import cfg


LOG = logging.getLogger(__name__)


def ensure_dir(path):
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except Exception:
        LOG.info("makdir %s failed", path)


class ProfilerHandler(object):
    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        taskid = req.headers['X-Neutron-Profiler-taskid']
        action = req.headers['X-Neutron-Profiler-Action']
        if action == 'start':
            # (anilvenkata): save self.taskid, helpful in throwing error
            # if stop called without start
            GreenletProfiler.set_clock_type('cpu')
            GreenletProfiler.start()
            LOG.info("Trace Profiler.start profiling %s ", os.getpid())
        elif action == 'stop':
            GreenletProfiler.stop()
            LOG.info("Trace Profiler.stop profiling %s ", os.getpid())
            stats = GreenletProfiler.get_func_stats()
            trace_path = os.path.join(
                cfg.CONF.trace_profiler.trace_path, taskid)
            ensure_dir(trace_path)
            trace_file = os.path.join(trace_path, str(os.getpid()))
            LOG.info("Trace Profiler.writing to trace file %s ", trace_file)
            stats.save(trace_file, cfg.CONF.trace_profiler.trace_format)
            GreenletProfiler.clear_stats()
        else:
            LOG.warning("Invalid profiler action %(action)s with "
                        " taskid %(taskid)s",
                        {"action": action, "taskid": taskid})


class ProfilerServer(object):

    def run(self):
        server = agent_utils.UnixDomainWSGIServer(
            'profiler-server')
        ensure_dir(cfg.CONF.trace_profiler.trace_path)
        ensure_dir(cfg.CONF.trace_profiler.sock_path)
        sock_path = os.path.join(cfg.CONF.trace_profiler.sock_path,
                                 str(os.getpid()))
        server.start(ProfilerHandler(), sock_path,
                     workers=0, backlog=4096)
        server.wait()


def start_profiler_server():
    LOG.info("Starting trace profiler server on process %s", os.getpid())
    profiler_server = ProfilerServer()
    profiler_server.run()
