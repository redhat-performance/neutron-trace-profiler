This package contains the code for the Neutron Profiler. This package requires Neutron to run.
It will make neutron processes(neutron API and RPC workers, l2 and l3 agents) to listen
on unix domain sockets for client's(rally, browbeat) requests to start and stop neutron
processes profiling(i.e capturing function call trace) during their tests.
This code is enabled in neutron server as service plugin and in agents(l2 and l3) as agent exentsions.
This is not enabled for dhcp agent as agent extensions are not enabled in dhcp agent.


Changes needed in neutron.conf(till devstack plugin enabled to do these changes):
# This will enable Trace profiler to regsiter for process 'AFTER_INIT' event.
# When this event is triggered(for each API/RPC worker), it will enable the worker
# process to create new unix socket(for profiler start and stop requests).

[DEFAULT]
service_plugins = neutron_trace_profiler.profiler.Profiler


[trace_profiler]
enabled = True
sock_path = /var/log/neutron/trace_profiler_sock
trace_path = /var/log/neutron/trace_profiler_files
trace_format = pstat


# This will enable trace profiler as agent extensions(for l2 and l3) and
# create a new trace profiler unix socket for the agent process.

[agent]
extensions = trace_profiler

User has to write to unix socket for profiling. Server expects below
request parameters
1) X-Neutron-Profiler-taskid: task name. A folder with this task id
is created in /var/log/neutron/trace_profiler_files and then trace files
are generated in this folder. If the client is rally, then pass rally taskid.

2) X-Neutron-Profiler-Action: can take start/snapshot/stop as values.
 start: To start profiling
 snapshot: Only applicable for objgraph and objcount profiling i.e
    generate objgraph now or capture python memory object count.
 stop: generate trace files

3) X-Neutron-Profiler-Type: Following profiling types supported
   a) calltrace: Generate function call trace
   b) objcount: Dump how many python objects(in neutron-server process)
                created between previous socket request and this request
   c) objgraph: Create objgraph(.dot file) for each python object
                (which exists after GC call) with its referrers
                 
4) X-Neutron-Profiler-Iteration: Introduced to capture objcount or
   objgraph after each rally iteration. A rally hook which writes to
   unix socket for profiling should pass iteration count. Non rally
   client should pass incremental number.

Example with 'nc' command to write to unix socket   

echo -e "POST /localhost/json HTTP/1.0\r\nX-Neutron-Profiler-taskid: taskid2\r\n
X-Neutron-Profiler-Action: start\r\n
X-Neutron-Profiler-Type: objcount\r\n
X-Neutron-Profiler-Iteration: 1\r\n" |
sudo nc -U /var/log/neutron/trace_profiler_sock/<neutron-server-pid>

TODO: Remove author names and convert it into openstack format.

