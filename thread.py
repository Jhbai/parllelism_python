class thread:
    def __init__(self, funcs, args, n_threads):
        """
        Create the threads, assign tasks and run them.
        example:
            >>> # assume u have N-times druid queries
            >>> # each parameter
            >>> def func(arg):
            >>>     ret = arg + 1
            >>>     return ret
            >>> N = 4
            >>> funcs = [func for i in range(N)]
            >>> args = [{"arg": i} for i in range(N-1)] + [{"args": "a"}]
            >>> data = thread(funcs, args, 4)
            >>> print(data.res)
            [1, 2, 3, 4]
            >>> print(data.fail)
            [{'msg': 'File "~/OOOO/XXXXXX.py", line 2, in func [TypeError]: can only concatenate str (not "int") to str', 'func': 'func', 'args': {'val': 'a'}}]
        The reason to use a class object is to record the error occurrence.

        :param funcs: A list of functions
        :param args: A list of arguments
        :param n_threads: How many threads will be used to run the jobs
        :return: None
        :attr res: A list of each function results
        :attr fail: A list of each fail logs
        """

        from threading import Thread, Lock
        import queue

        # Assign all the parameters that will be used
        self.lock = Lock()
        self.task_queue = queue.Queue()
        self.task_queue.queue.extend([(f, p) for f, p in zip(funcs, args)])
        self.threads = list()
        self.res = queue.Queue()
        self.fail = queue.Queue()

        # Create a lot of threads and start them
        for _ in range(n_threads):
            t = Thread(target=self.job)
            t.start()
            self.threads += [t]

        # Clean the resource
        self.task_queue.join()
        for t in self.threads:
            t.join()
        self.res = list(self.res.queue)
        self.fail = list(self.fail.queue)

    def job(self):
        import queue
        while True:
            try:
                task, args = self.task_queue.get(timeout=0)
                try:
                    result = task(**args)
                    self.res.put(result)
                except Exception as e:
                    self.fail.put({"msg": self.exceptionMsg(e), "func": task.__name__, "args": args})
            except queue.Empty:
                break

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
    T = thread(funcs = [func]*10, args = [{"val": i} for i in range(9)] + [{"val": "a"}], n_threads = 4)
    print("[Output]", T.res)
    print("[Error]", T.fail)