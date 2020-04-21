# # Project Workflow
# Goal: Manage Workflow and related middlewares
# TODO: Add Simple scalable plugin system


class SharedTasks():

    tasks = {
        "taskname": {}
    }

    plugins = {
        "pluginname": {
            "taskname": {}
        }
    }

    __instance = None

    def __init__(self):

        # Option 1:
        if SharedTasks.__instance != None:
            # raise Exception("In case erring out is needed - This class is a singleton!")
            pass
        else:
            SharedTasks.__instance = self

        # Option 3: This is okay due to implementation of __new__
        # pass

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(SharedTasks, cls).__new__(cls)
            # Note needed currently: Put any initialization code here
        return cls.__instance

    @staticmethod
    def getInstance():
        """ Static access method. """
        if not SharedTasks.__instance:
            SharedTasks()
        return SharedTasks.__instance


class WorkflowBase():

    tasks = {
        "taskname": {}
    }

    plugins = {
        "pluginname": {
            "taskname": {}
        }
    }

    def __init__(self):
        self.shared_tasks = SharedTasks.getInstance()
        # print("Workflow Creating the global object", self.globals)

    def __run_middleware(self, fn, error_obj, log, *args, **kwargs):

        try:
            if log:
                print("Workflow running middleware function: ", fn.__name__)
            return True, fn(*args, **kwargs)

        except Exception as e:
            if log:
                print("Running error for middleware")

            if not hasattr(error_obj, "error"):
                error_obj["error"] = "exit"

            ero = error_obj.get("error")
            erno = error_obj.get("error_next_value")

            if ero == "next":
                return 'next', (e, erno)
            elif ero == "error_handler":
                if not hasattr(error_obj, "error_handler"):
                    return "error_handler", (e, erno)
                return 'error_handler', error_obj.get("error_handler")(e, erno)
            elif ero == "exit":
                raise Exception("error_obj['error'] exit: Error during middleware: ",
                                fn.__name__, str(e))
            else:
                raise Exception(
                    "Error during middleware: flow[options[error]] value error")

    def __get_md_args(self, f, action, log):

        if action and isinstance(action, dict):
            a, kwa, err_obj = [], {}, {}
            if "args" in action and isinstance(action.get("args"), list):
                a = action.get("args")
            if "kwargs" in action and isinstance(action.get("kwargs"), dict):
                kwa = action.get("kwargs")
            if "options" in action and isinstance(action.get("options"), dict):
                err_obj = action.get("options")

        # TODO: Do clean args here
        return err_obj, a, kwa

    def __setup_run_middleware(self, task, md_action, log):

        #       Iterate through before/after for each task
        #           trigger before functions with next or handle error
        #           with error_handler, next or exit based on options

        actions = task.get("wf_kwargs").get(md_action)
        log = task.get("wf_kwargs").get("log")

        if actions and isinstance(actions, list):
            for action in actions:
                fn = action.get("function")
                err_obj, a, kwa = self.__get_md_args(fn, action, log)
                self.__run_middleware(fn, err_obj, log, *a, **kwa)
        elif actions and isinstance(actions, dict):
            err_obj, a, kwa = self.__get_md_args(
                actions.get("function"), actions, log)
            self.__run_middleware(actions.get("function"),
                                  err_obj, log, *a, **kwa)

    def clean_args(self, fn, wf_args, wf_kwargs, fn_a, fn_kwa):

        tpl = fn.__code__.co_varnames
        k_fn_kwa = fn_kwa.keys()
        l_tpl, l_fn_a, l_k_fn_kwa = len(tpl), len(fn_a), len(k_fn_kwa)

        if (l_tpl == l_fn_a + l_k_fn_kwa):
            for k in k_fn_kwa:
                if not tpl.index(k) >= l_fn_a:
                    return False
            return True
        return False

    def get_tasks(self, task=None, shared=False):

        # get shared if shared is requested
        if shared and task and isinstance(task, str):
            return self.shared_tasks.tasks.get(task)
        elif not shared and task and isinstance(task, str):
            return self.tasks.get(task)
        return self.tasks

    def set_task(self, fn, fn_a, fn_kwa, wf_args, wf_kwargs):

        wfname = wf_kwargs.get("name")
        print("Workflow task name to add: ", wfname)

        shared = wf_kwargs.get("shared")

        # set in global or local
        if shared == True:
            if wfname not in self.shared_tasks.tasks.keys():
                self.shared_tasks.tasks[wfname] = {}
            if not isinstance(self.shared_tasks.tasks[wfname], dict):
                self.shared_tasks.tasks.update({wfname: {}})

        elif not shared == True:
            if wfname not in self.tasks.keys():
                self.tasks[wfname] = {}
            if not isinstance(self.tasks[wfname], dict):
                self.tasks.update({wfname: {}})

        self.tasks[wfname].update({
            "task_order": wf_kwargs.get("task_order"),
            "wf_args": wf_args, "wf_kwargs": wf_kwargs,
            "fn_a": fn_a, "fn_kwa": fn_kwa,
            "before": wf_kwargs.get("before"),
            "after": wf_kwargs.get("after"),
            "function": fn,
            "log": wf_kwargs.get("log")
        })

        print("Workflow set_task: Adding Task: ", wfname)
        # print("Workflow set_task: ", tasks[kwargs["name"]][kwargs["task_order"]])

    def get_task_attr(self, task, attr):
        if not task.get(attr):
            if not task.get("shared"):
                task[attr] = self.tasks.get(attr)
            elif task.get("shared"):
                task[attr] = self.shared_tasks.tasks.get(attr)
            else:
                raise Exception(
                    "Workflow get_task_attr: shared value and task attribute presence error")
        return task.get(attr)

    def update_task(self, task):

        # task object structure
        # name, args, task_order, shared, before, after, function, fn_a, fn_kwa, log
        """wf_kwargs: name, args, task_order, shared, before, after, log"""

        task_obj = {
            "task_order": self.get_task_attr(task, "task_order"),
            "wf_args": self.get_task_attr(task, "args"),
            "wf_kwargs": self.get_task_attr(task, "wf_kwargs"),
            "fn_a": self.get_task_attr(task, "fn_a"),
            "fn_kwa": self.get_task_attr(task, "fn_args"),
            "before": self.get_task_attr(task, "before"),
            "after": self.get_task_attr(task, "after"),
            "function": self.get_task_attr(task, "function"),
            "log": self.get_task_attr(task, "log")
        }

        if task.get("shared") == True:
            self.shared_tasks.tasks.update(task.get("name"), task_obj)
        elif task.get("shared") == False:
            self.tasks.update(task.get("name"), task_obj)

    def run_task(self, task, shared=None):
        # task object structure
        # name, args, task_order, shared, before, after, function, fn_a, fn_kwa, log
        """wf_kwargs: name, args, task_order, shared, before, after, log"""

        tsk = self.get_tasks(task, shared)
        log = tsk.get("log")

        if log:
            print("Workflow task found: ", task)
            # print("The workflow object looks like this: ", tsk)

        if tsk:
            # TODO: Put in try except block for clean errors

            #       Iterate through before for each task
            if log:
                print("Workflow before middlewares for task now running: ",
                      task)
            self.__setup_run_middleware(tsk, "before", log)

            #       Invoke task
            if log:
                print("Workflow task run: ", task)
            tsk.get("function")(*tsk.get("fn_a"), **tsk.get("fn_kwa"))

            #       Iterate through after for each task
            if log:
                print("Workflow after middlewares for task now running: ",
                      task)
            self.__setup_run_middleware(tsk, "after", log)

    def __merge_instance(self, tasks, inst, shared=None, clash_prefix=None):
        for k in tasks.keys():
            for ik in inst.tasks.keys():
                if k == ik:
                    if not clash_prefix:
                        raise Exception(
                            "Workflow merge_instance: clash_prefix not provided")
                    tasks.update(clash_prefix + ik, inst.tasks.get(ik))
                tasks[ik] = inst.tasks.get(ik)
        return tasks

    def merge_instance(self, inst, shared=False, clash_prefix=None):
        if shared == True:
            self.shared_tasks.tasks = self.__merge_instance(
                self.shared_tasks.tasks, inst, clash_prefix)
        elif shared == False:
            self.tasks = self.__merge_instance(
                self.tasks, inst, shared, clash_prefix)


class Tasks(WorkflowBase):

    def add_plugin(self, plugin_inst):
        pass

    def merge(self, inst, shared=False, clash_prefix=None):
        self.merge_instance(inst, shared, clash_prefix)

    def run(self, tasks):

        if isinstance(tasks, str):
            # Iterate task through single task
            print("Workflow task provided being instantiated: ", str(tasks))
            print("Workflow has tasks: ", str(self.tasks.keys()))
            self.run_task(tasks)

        elif isinstance(tasks, list):
            # Iterate task through tasks
            print("Workflow task list provided being instantiated: ", str(tasks))
            print("Workflow has tasks: ", str(self.tasks.keys()))
            [self.run_task(t) for t in self.tasks]

        else:
            print("No workflow or task available to run")

    def apis(self):

        return {
            "get_tasks": self.get_tasks,
            "set_task": self.set_task,
            "update_task": self.update_task,
            "run_task": self.run_task,
            "clean_args": self.clean_args
        }


def workflow(*wf_args, **wf_kwargs):

    def get_decorator(fn):
        # print("get_decorator: Decorator init ", "wf_args: ", wf_args, "wf_kwargs: ", wf_kwargs)
        # print("get_decorator: ", fn)

        def order_tasks(*fn_a, **fn_kwa):
            # print("Workflow order_tasks: Decorator init ", "fn_a: ", fn_a, "fn_kwa: ", fn_kwa)

            t = wf_kwargs.get("task_instance")
            if not t:
                raise Exception("Task instance not provided")

            # Check before/after middlewares args and kwargs number and validity
            args_normal = t.clean_args(fn, wf_args, wf_kwargs, fn_a, fn_kwa)

            if not args_normal:
                raise Exception("Args and KwArgs do not match")

            # print((fn, fn_a, fn_kwa, wf_args, wf_kwargs))
            t.set_task(fn, fn_a, fn_kwa, wf_args, wf_kwargs)

            print("Workflow order_tasks - Task added: ", wf_kwargs.get("name"))

        return order_tasks
    return get_decorator


__all__ = ["Tasks", "workflow"]
