import GreenletProfiler
import logging
import os
import webob.dec
import webob.exc

from neutron._i18n import _LI
from neutron.agent.linux import utils as agent_utils
from neutron.common import utils
from oslo_config import cfg


LOG = logging.getLogger(__name__)


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
            LOG.debug("Trace Profiler.start profiling %s ", os.getpid())
        elif action == 'stop':
            GreenletProfiler.stop()
            LOG.debug("Trace Profiler.stop profiling %s ", os.getpid())
            stats = GreenletProfiler.get_func_stats()
            trace_path = os.path.join(
                cfg.CONF.trace_profiler.trace_path, taskid)
            utils.ensure_dir(trace_path)
            trace_file = os.path.join(trace_path, str(os.getpid()))
            LOG.debug("Trace Profiler.writing to trace file %s ", trace_file)
            stats.save(trace_file, cfg.CONF.trace_profiler.trace_format)
            GreenletProfiler.clear_stats()
        else:
            LOG.info(_LI("Invalid profiler action %(action)s with "
                         " taskid %(taskid)s"),
                     {"action": action, "taskid": taskid})


class ProfilerServer(object):

    @classmethod
    def get_profiler_sock_path(cls):
        utils.ensure_dir(cfg.CONF.trace_profiler.sock_path)
        return os.path.join(cfg.CONF.trace_profiler.sock_path,
                            str(os.getpid()))

    def run(self):
        server = agent_utils.UnixDomainWSGIServer(
            'profiler-server')
        server.start(ProfilerHandler(),
                     self.get_profiler_sock_path(),
                     workers=0,
                     backlog=4096)
        server.wait()


def start_profiler_server():
    LOG.debug("Starting trace profiler server on process %s", os.getpid())
    profiler_server = ProfilerServer()
    profiler_server.run()
