#!/usr/bin/python3

from bcc import BPF
import json
import datetime
import time

# BPF program
bpf_program = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>
#include <linux/limits.h>

BPF_PERF_OUTPUT(bpf_buffer_00);

struct execve_data_t {
    u64 ts;
    u64 uid;
    u32 pid;
    u32 ppid;
    char comm[TASK_COMM_LEN];
    char filename[NAME_MAX];
};

TRACEPOINT_PROBE(syscalls, sys_enter_execve) {

    struct execve_data_t data = {};

    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    data.ppid = task->real_parent->tgid;

    u32 pid = (u32)(bpf_get_current_pid_tgid() >> 32);
    data.pid = pid;
    data.uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    bpf_probe_read_user_str(&data.filename, sizeof(data.filename), args->filename);
    data.ts = bpf_ktime_get_ns();
    bpf_buffer_00.perf_submit(args, &data, sizeof(data));

    return 0;
}
"""

# Load BPF program
bpf = BPF(text=bpf_program)
bpf.detach_tracepoint("syscalls:sys_enter_execve")

# Attach the BPF program to the sys_enter_execve tracepoint
bpf.attach_tracepoint(tp="syscalls:sys_enter_execve", fn_name="tracepoint__syscalls__sys_enter_execve")

time_nanosec = time.time_ns()

def nanoseconds_to_datetime(nanoseconds):
    seconds = nanoseconds / 1e9
    dt = datetime.datetime.utcfromtimestamp(seconds)
    readable_time = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Trim to milliseconds
    return readable_time

def print_event(cpu, data, size):
    event = bpf["bpf_buffer_00"].event(data)
    dj = json.dumps({
       "ppid": event.ppid,
       "pid": event.pid,
       "uid": event.uid,
       "comm": event.comm.decode('utf-8', 'replace'),
       "filename": event.filename.decode('utf-8', 'replace'),
       "utcdatetime": nanoseconds_to_datetime(time_nanosec - event.ts),
       "monots": event.ts,
    })
    print(dj)

bpf["bpf_buffer_00"].open_perf_buffer(print_event)

print("Tracing execve... Press Ctrl+C to stop.")

# Poll the perf buffer to process events
while True:
    try:
        bpf.perf_buffer_poll()
    except KeyboardInterrupt:
        exit()
