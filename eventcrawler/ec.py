#!/usr/bin/python3

from bcc import BPF
import json
import os


program = r"""
BPF_PERF_OUTPUT(output);

#include <linux/sched.h>

struct data_t {
   int pid;
   int ppid;
   int uid;
   char command[16];
   char message[12];
};

int grab_execution(void *ctx) {
   struct data_t data = {};
   char message[12] = "No timestamp";

   struct task_struct *task = (struct task_struct *)bpf_get_current_task();
   data.ppid = task->real_parent->tgid;

   data.pid = bpf_get_current_pid_tgid() >> 32;
   data.uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;

   bpf_get_current_comm(&data.command, sizeof(data.command));
   bpf_probe_read_kernel(&data.message, sizeof(data.message), message);

   output.perf_submit(ctx, &data, sizeof(data));

   return 0;
}
"""

b = BPF(text=program)
syscall = b.get_syscall_fnname("execve")
b.attach_kprobe(event=syscall, fn_name="grab_execution")

fetch_pathname = lambda pid: os.readlink(f"/proc/{pid}/exe")

def fetch_cmdline(pid):
   cmd_line = None
   with open(f"/proc/{pid}/cmdline") as fr:
       return fr.readline()

def print_event(cpu, data, size):
   data = b["output"].event(data)
   dj = json.dumps({
       "ppid": data.ppid,
       "pid": data.pid,
       "uid": data.uid,
       "cmd": data.command.decode(),
       "path_name": fetch_pathname(data.pid),
       "cmd_line": fetch_cmdline(data.pid),
       "msg": data.message.decode(),
   })
   print(dj)

b["output"].open_perf_buffer(print_event)
while True:
   b.perf_buffer_poll()
