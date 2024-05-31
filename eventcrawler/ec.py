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

BPF_PERF_OUTPUT(PERF_BUFFER_00);

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
    PERF_BUFFER_00.perf_submit(args, &data, sizeof(data));

    return 0;
}
"""

class EventCrawler(object):

    __BPF_PERF = "PERF_BUFFER_00"
    __TP_HOOK = "sys_enter_execve"
    __TP_FN = f"tracepoint__syscalls__{__TP_HOOK}"
    __TP_SYSCALL = f"syscalls:{__TP_HOOK}"

    def __init__(self, prog_src):
        self._prog_src = prog_src
        self._time_increment = 0

    @classmethod
    def spinup(cls, prog_src):
        print("Tracing execve... Press Ctrl+C to stop.")
        try:
            crawler = cls(bpf_program)
            crawler._engage()
        except KeyboardInterrupt:
            exit(0)

    def _setup_bpf(self):
        self._bpf = BPF(text=self._prog_src)
        self._bpf.detach_tracepoint(self.__TP_SYSCALL)
        self._bpf.attach_tracepoint(tp=self.__TP_SYSCALL, fn_name=self.__TP_FN)
        self._bpf[self.__BPF_PERF].open_perf_buffer(self._print_event)

    def _engage(self):
        '''Blocks as long as it reads buffer'''
        self._setup_bpf()
        self._time_nanosec = time.time_ns()
        while True:
            self._bpf.perf_buffer_poll()

    @staticmethod
    def _nanoseconds_to_datetime(nanoseconds):
        seconds = nanoseconds / 1e9
        dt = datetime.datetime.utcfromtimestamp(seconds)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Trim to milliseconds

    def _print_event(self, cpu, data, size):
        event = self._bpf[self.__BPF_PERF].event(data)
        if self._time_increment > 0:
            self._time_increment = event.ts - self._time_increment
        self._time_nanosec += self._time_increment
        dj = json.dumps({
           "ppid": event.ppid,
           "pid": event.pid,
           "uid": event.uid,
           "comm": event.comm.decode('utf-8', 'replace'),
           "filename": event.filename.decode('utf-8', 'replace'),
           "utcdatetime": self._nanoseconds_to_datetime(self._time_nanosec),
           "monots": event.ts,
        })
        self._time_increment = event.ts
        print(dj)

if __name__ == "__main__":
    EventCrawler.spinup(bpf_program)
