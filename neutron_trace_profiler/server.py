import gc
import GreenletProfiler
import inspect
import json
import logging
import objgraph
import os
import socket
import webob.dec
import webob.exc

from oslo_config import cfg
from oslo_service import wsgi


LOG = logging.getLogger(__name__)

objcount_dict = {}


def ensure_dir(path):
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except Exception:
        LOG.info("makdir %s failed", path)
        pass


def dump_objgrpah(objgraph_file):
    new_ids = objgraph.get_new_ids()
    new_ids_list = new_ids['list']
    new_objs = objgraph.at_addrs(new_ids_list)
    objgraph.show_backrefs(new_objs, highlight=inspect.isclass,
                           refcounts=True, filename=objgraph_file)
    new_ids = objgraph.get_new_ids()


class ProfilerHandler(object):
    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        taskid = req.headers['X-Neutron-Profiler-taskid']
        action = req.headers['X-Neutron-Profiler-Action']
        iteration = req.headers.get('X-Neutron-Profiler-Iteration')
        profiler_type = req.headers.get('X-Neutron-Profiler-Type')
        obj_graph = True if profiler_type == 'objgraph' else False
        objcount = (True if (profiler_type in ['objcount', 'objgraph'])
                    else False)
        calltrace = (True
                     if (not profiler_type or profiler_type == 'calltrace')
                     else False)
        trace_path = os.path.join(
            cfg.CONF.trace_profiler.trace_path, taskid)
        ensure_dir(trace_path)
        LOG.info("Trace Profiler pid %s taskid %s action %s iteration %s"
                 " profiler_type %s",
                 os.getpid(), taskid, action, iteration, profiler_type)
        if action == 'start':
            if calltrace:
                GreenletProfiler.set_clock_type('cpu')
                GreenletProfiler.start()
            if objcount and iteration:
                objcount_dict[iteration] = len(gc.get_objects())
            if obj_graph:
                objgraph.get_new_ids()
            LOG.info("Trace Profiler.start profiling %s ", os.getpid())
        elif action == 'snapshot':
            if iteration:
                if objcount:
                    objcount_dict[iteration] = len(gc.get_objects())
                if obj_graph:
                    objgraph_file = os.path.join(
                        trace_path, "{}-{}-{}-objgraph.dot".format(
                            socket.gethostname(), os.getpid(), iteration))
                    dump_objgrpah(objgraph_file)
        elif action == 'stop':
            LOG.info("Trace Profiler.stop profiling %s ", os.getpid())
            if calltrace:
                trace_file = os.path.join(
                    trace_path, "{}-{}".format(socket.gethostname(),
                                               os.getpid()))
                GreenletProfiler.stop()
                stats = GreenletProfiler.get_func_stats()
                LOG.info("Trace Profiler.writing to trace file %s ",
                         trace_file)
                stats.save(trace_file, cfg.CONF.trace_profiler.trace_format)
                GreenletProfiler.clear_stats()
            if objcount:
                objcount_file = os.path.join(
                    trace_path, "{}-{}-objcount".format(socket.gethostname(),
                                                        os.getpid()))
                if iteration:
                    objcount_dict[iteration] = len(gc.get_objects())
                with open(objcount_file, 'w') as fp:
                    json.dump(objcount_dict, fp)
                objcount_dict.clear()
            if obj_graph:
                objgraph_file = os.path.join(
                    trace_path, "{}-{}-objgraph.dot".format(
                        socket.gethostname(), os.getpid()))
                dump_objgrpah(objgraph_file)
        else:
            LOG.warning("Invalid profiler action %(action)s with "
                        " taskid %(taskid)s",
                        {"action": action, "taskid": taskid})


class ProfilerServer(object):

    def run(self):
        ensure_dir(cfg.CONF.trace_profiler.trace_path)
        ensure_dir(cfg.CONF.trace_profiler.sock_path)
        sock_path = os.path.join(cfg.CONF.trace_profiler.sock_path,
                                 str(os.getpid()))
        socket_mode = 0o666
        server = wsgi.Server(cfg.CONF, "profiler-server", ProfilerHandler(),
                             socket_family=socket.AF_UNIX,
                             socket_mode=socket_mode,
                             socket_file=sock_path)
        server.start()
        server.wait()


def start_profiler_server():
    LOG.info("Starting trace profiler server on process %s", os.getpid())
    profiler_server = ProfilerServer()
    profiler_server.run()
