import gc
import GreenletProfiler
import json
import logging
import os
import socket
import webob.dec
import webob.exc

from neutron.agent.linux import utils as agent_utils
from oslo_config import cfg


LOG = logging.getLogger(__name__)

obj_count = {}


def ensure_dir(path):
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except Exception:
        LOG.info("makdir %s failed", path)
        pass


class ProfilerHandler(object):
    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        taskid = req.headers['X-Neutron-Profiler-taskid']
        action = req.headers['X-Neutron-Profiler-Action']
        iteration = req.headers.get('X-Neutron-Profiler-Iteration')
        profiler_type = req.headers.get('X-Neutron-Profiler-Type')
        if not profiler_type:
            profiler_type = 'calltrace'
        LOG.info("Trace Profiler pid %s taskid %s action %s iteration %s"
                 " profiler_type %s",
                 os.getpid(), taskid, action, iteration, profiler_type)
        if action == 'start':
            if profiler_type == 'calltrace':
                GreenletProfiler.set_clock_type('cpu')
                GreenletProfiler.start()
            else:
                if iteration:
                    obj_count[iteration] = len(gc.get_objects())
            LOG.info("anil Trace Profiler.start profiling %s ", os.getpid())
        if action == 'snapshot':
            if iteration and profiler_type == 'memory':
                obj_count[iteration] = len(gc.get_objects())
        elif action == 'stop':
            LOG.info("anil Trace Profiler.stop profiling %s ", os.getpid())
            trace_path = os.path.join(
                cfg.CONF.trace_profiler.trace_path, taskid)
            ensure_dir(trace_path)
            trace_file = os.path.join(
                trace_path, "{}-{}".format(socket.gethostname(), os.getpid()))
            if profiler_type == 'calltrace':
                GreenletProfiler.stop()
                stats = GreenletProfiler.get_func_stats()
                LOG.info("Trace Profiler.writing to trace file %s ",
                         trace_file)
                stats.save(trace_file, cfg.CONF.trace_profiler.trace_format)
                GreenletProfiler.clear_stats()
            else:
                obj_file = os.path.join(
                    trace_path, "{}-{}-objcount".format(socket.gethostname(),
                                                        os.getpid()))
                if iteration:
                    obj_count[iteration] = len(gc.get_objects())
                with open(obj_file, 'w') as fp:
                    json.dump(obj_count, fp)

                obj_count.clear()
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
