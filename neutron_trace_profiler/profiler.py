import logging
import server
import threading

from neutron_lib.agent import extension
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.callbacks import resources
from neutron_lib.services import base as service_base
from oslo_config import cfg


LOG = logging.getLogger(__name__)

PROFILER_PLUGIN_TYPE = 'TRACE_PROFILER'
PROFILER_SOCK_DIR = '/var/log/neutron/trace_profiler_sock'
PROFILER_TRACE_DIR = '/var/log/neutron/trace_profiler_files'
TRACE_FORMAT = 'pstat'

ProfilerOpts = [
    cfg.StrOpt(
        'sock_path',
        default=PROFILER_SOCK_DIR,
        help=_("Profiler socket path")),
    cfg.BoolOpt(
        'enabled',
        default=True,
        help=_("Enable Trace Profiler")),
    cfg.StrOpt(
        'trace_format',
        default=TRACE_FORMAT,
        help=_("Profiler trace format")),
    cfg.StrOpt(
        'trace_path',
        default=PROFILER_TRACE_DIR,
        help=_("Profiler trace files path")),
]
cfg.CONF.register_opts(ProfilerOpts, 'trace_profiler')


class Profiler(service_base.ServicePluginBase):
    def __init__(self):
        super(Profiler, self).__init__()
        if cfg.CONF.trace_profiler.enabled:
            self.subscribe()

    @classmethod
    def get_plugin_type(cls):
        return PROFILER_PLUGIN_TYPE

    def get_plugin_description(self):
        return "Neutron trace profiler plugin"

    def subscribe(self):
        registry.subscribe(
            process_spawned, resources.PROCESS, events.AFTER_INIT)


def process_spawned(resource, event, trigger, **kwargs):
    thread = threading.Thread(target=server.start_profiler_server)
    thread.start()


class ProfilerAgentExtension(extension.AgentExtension):
    def initialize(self, connection, driver_type):
        thread = threading.Thread(target=server.start_profiler_server)
        thread.start()

    def consume_api(self, agent_api):
        pass
