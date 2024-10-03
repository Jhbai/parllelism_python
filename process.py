class process:
    def __init__(self, funcs, args, n_proc):
        """
        Create the processes, assign tasks and run them.
        example:
            >>> # assume u have N-times druid queries
            >>> # each parameter
            >>> def func(arg):
            >>>     ret = arg + 1
            >>>     return ret
            >>> N = 4
            >>> funcs = [func for i in range(N)]
            >>> args = [{"arg": i} for i in range(N-1)] + [{"args": "a"}]
            >>> data = process(funcs, args, 4)
            >>> print(data.res)
            [1, 2, 3, 4]
            >>> print(data.fail)
            [{'msg': 'File "~/OOOO/XXXXXX.py", line 2, in func [TypeError]: can only concatenate str (not "int") to str', 'func': 'func', 'args': {'val': 'a'}}]
        The reason to use a class object is to record the error occurrence.
        This object use fork and pipe to implement process creation and IPC.
        Using set flags to signal "EAGAIN" or "EWOULDBLOCK" to interrupt(sys call).

        :param funcs: A list of functions
        :param args: A list of arguments
        :param n_proc: How many processes will be used to run the jobs
        :return: None
        :attr res: A list of each function results
        :attr fail: A list of each fail logs
        """

        # Package import
        import os
        import struct
        import pickle
        
        # Job, children management variables created
        n_jobs = len(funcs)
        jobs = list()
        active_processes = dict()

        # result
        self.res = list()

        # Job object created
        for i in range(n_jobs):
            fds = os.pipe()
            jobs += [(fds, funcs[i], args[i])]
        
        # Processes fork, There are two parts
        # A while loop to check whether there is still job remaining or all the processes have completed.
        # The first part is if not all the jobs are finished and processes amount is less than n_proc, then assign a new job to execute
        # The second part is if wait until 
        while jobs or active_processes:
            # First part
            # If there are still jobs remain and there is still some processes quota as well, assign a process to run on it
            if jobs and len(active_processes) < n_proc:
                fd, func, arg = jobs.pop(0)
                pid = os.fork()
                if pid == 0:
                    self.job(fd, func, arg)
                    os._exit(0)
                else:
                    active_processes[pid] = fd[0]
            
            # Second part
            # Nonblockingly check whether children finish, to avoid zombie processes and manage the amount of running processes
            for pid in list(active_processes):
                finished_pid, _ = os.waitpid(pid, os.WNOHANG)
                if finished_pid:
                    # Read the result
                    fd = active_processes[finished_pid]
                    data_length = os.read(fd, 4)
                    data_length = struct.unpack('I', data_length)[0]
                    self.res += [pickle.loads(os.read(fd, data_length))]
                    os.close(fd)

                    # Clean the finished child
                    active_processes.pop(finished_pid) 



    def job(self, fd, func, arg):
        import os
        import struct
        import pickle
        try:
            res = func(**arg)
        except Exception as e:
            res = self.exceptionMsg(e)
        res = pickle.dumps(res)
        os.write(fd[1], struct.pack('I', len(res)))
        os.write(fd[1], res) 
        os.close(fd[1])

    @staticmethod
    def exceptionMsg(e):
        import sys, os, traceback
        error_class = e.__class__.__name__  # Get the error type
        detail = e.args[0]  # Get the detailed info
        cl, exc, tb = sys.exc_info()  # Get the call stack
        lastCallStack = traceback.extract_tb(tb)[-1]  # Get the final call from the call stack, {0: file name, 1: lineno, 2: func name}
        errMsg = "File \"{}\", line {}, in {} [{}]: {}".format(lastCallStack[0], lastCallStack[1], lastCallStack[2], error_class, detail)
        return errMsg
    
if __name__ == "__main__":
    def func(val):
        return val + 1
    P = process(funcs = [func]*10, args = [{"val": i} for i in range(9)] + [{"val": "a"}], n_proc = 4)
    print(P.res)