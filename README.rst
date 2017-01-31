This package contains the code for the Neutron Profiler. This package requires Neutron to run.
It will make neutron processes(neutron API and RPC workers, l2 and l3 agents) to listen
on unix domain sockets for client's(rally, browbeat) requests to start and stop neutron
processes profiling during their tests.

Changes needed in neutron.conf(till devstack plugin enabled to do these changes):
# This will enable Trace profiler to regsiter for process 'AFTER_INIT' event.
# When this event is triggered(for each API/RPC worker), it will enable the worker
# process to create new unix socket(for profiler start and stop requests).
[DEFAULT]
service_plugins = neutron_trace_profiler.profiler.Profiler

[trace_profiler]
enabled = True
sock_path = /opt/stack/data/neutron/trace_profiler_sock
trace_path = /opt/stack/data/neutron/trace_profiler_files
trace_format = pstat

# This will enable trace profiler as agent extensions(for l2 and l3) and
# create a new trace profiler unix socket for the agent process.
[agent]
extensions = trace_profiler



