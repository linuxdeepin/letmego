#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
import inspect
import os
import re
import threading
import weakref
from functools import wraps
from letmego.conf import setting


class Singleton(type):
    """Singleton"""

    _instance_lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Singleton.__instance = None
        self._cache = weakref.WeakValueDictionary()

    def __call__(self, *args, **kwargs):
        kargs = "".join([f"{key}" for key in args]) if args else ""
        kkwargs = "".join([f"{key}" for key in kwargs]) if kwargs else ""
        if kargs + kkwargs not in self._cache:
            with Singleton._instance_lock:
                Singleton.__instance = super().__call__(*args, **kwargs)
                self._cache[kargs + kkwargs] = Singleton.__instance
        else:
            Singleton.__instance = self._cache[kargs + kkwargs]
        return Singleton.__instance


def is_static_method(klass_or_instance, attr: str):
    """
    Test if a value of a class is static method
    :param klass_or_instance: the class
    :param attr: attribute name
    """
    if attr.startswith("_"):
        return False
    value = getattr(klass_or_instance, attr)
    if inspect.isroutine(value):
        if isinstance(value, property):
            return False
        args = []
        for param in inspect.signature(value).parameters.values():
            kind = param.kind
            name = param.name
            if kind is inspect._ParameterKind.POSITIONAL_ONLY:
                args.append(name)
            elif kind is inspect._ParameterKind.POSITIONAL_OR_KEYWORD:
                args.append(name)
        if len(args) == 0:
            return True
        if args[0] == "self":
            return False
        return inspect.isfunction(value)
    return False


def _trace(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            if (
                    isinstance(args[0], inspect._findclass(func))
                    and func.__name__ != "__init__"
            ):
                if func:
                    if any(
                            [
                                inspect.ismethod(func),
                                is_static_method(
                                    inspect._findclass(func),
                                    func.__name__,
                                ),
                            ]
                    ):
                        args = list(args)[1:]
        except IndexError:
            pass
        frame = inspect.currentframe()
        case_filename = str(frame.f_back.f_code.co_filename)
        if not case_filename.split("/")[-1].startswith("test"):
            return func(*args, **kwargs)
        page_class_name = inspect._findclass(func).__name__
        page_func_name = func.__name__
        if page_func_name == "__init__":
            return func(*args, **kwargs)
        page_func_line = str(frame.f_back.f_lineno)
        case_func_name = str(frame.f_back.f_code.co_name)
        case_class_name = re.findall(
            rf"<.*?\.{setting.TARGET_FILE_STARTSWITH}.*?\.(.*?) object at .*?>",
            str(frame.f_back.f_locals.get("self"))
        )
        if case_class_name:
            case_class_name = case_class_name[0]
        running_man = (
            f"{case_filename}-{case_class_name}-{case_func_name}-{page_class_name}-{page_func_name}-{page_func_line}"
        )
        if setting.EXECUTION_COUNT:
            running_man = f"{running_man}-{setting.EXECUTION_COUNT}"
        marks = []
        running_man_file = os.path.expanduser(setting.RUNNING_MAN_FILE)
        if os.path.exists(running_man_file):
            with open(running_man_file, "r", encoding="utf-8") as f:
                marks = f.readlines()
        if f"{running_man}\n" not in marks:
            with open(running_man_file, "a+", encoding="utf-8") as f:
                f.write(f"{running_man}\n")
        else:
            return None
        return func(*args, **kwargs)

    return wrapped


def mark(cls):
    """
    class decorator
    example:
    ===============================
    @letmego.mark
    class Page:
        def click_some_element():
            ...
    ===============================
    :param cls: class object
    :return: class object
    """
    for name, obj in inspect.getmembers(
            cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x)
    ):
        if hasattr(getattr(cls, name), "__letmego"):
            if not getattr(cls, name).__letmego:
                setattr(cls, name, _trace(obj))
                setattr(getattr(cls, name), "__letmego", True)
        else:
            setattr(cls, name, _trace(obj))
            setattr(getattr(cls, name), "__letmego", True)
    return cls


_service_template = """[Unit]
Description=Test Service
After=multi-user.target

[Service]
User={user}
Group={user}
Type=idle
Environment=XDG_RUNTIME_DIR=/run/user/1000
WorkingDirectory={working_directory}
ExecStart={cmd}

[Install]
WantedBy=multi-user.target
"""


def register_autostart_service(user: str, working_directory: str, cmd: str):
    """
    register autostart service
    need password
    example:
    ===================================
    register_autostart_service(
        user="uos",
        working_directory="/home/uos/",
        cmd="ls"
    )
    ===================================
    :param user: os user
    :param working_directory: working directory
    :param cmd: cmd
    :return:
    """
    service = _service_template.format(user=user, working_directory=working_directory, cmd=cmd)
    service_file = f"/tmp/{setting.PROJECT_NAME}.service"
    with open(service_file, "w", encoding="utf-8") as f:
        f.write(service)
    os.system(f"echo '{setting.PASSWORD}' | sudo -S mv {service_file} /lib/systemd/system/")
    os.system(f"echo '{setting.PASSWORD}' | sudo -S chmod 644 /lib/systemd/system/{setting.PROJECT_NAME}.service")
    os.system(f"echo '{setting.PASSWORD}' | sudo -S systemctl daemon-reload")
    os.system(f"echo '{setting.PASSWORD}' | sudo -S systemctl enable {setting.PROJECT_NAME}.service")


def unregister_autostart_service():
    """
    register autostart service
    need password
    :return: None
    """
    os.system(f"cho '{setting.PASSWORD}' | sudo -S rm -rf /lib/systemd/system/{setting.PROJECT_NAME}.service")


def clean_running_man(copy_to=None):
    """clean running man file"""
    if copy_to:
        os.system(f"cp {setting.RUNNING_MAN_FILE} {copy_to}")
    os.system(f"rm -rf {setting.RUNNING_MAN_FILE}")


def write_testcase_running_status(item, report=None):
    """
    write testcase running status
    :param item: pytest item object
    :return:
    """
    with open(os.path.expanduser(setting.RUNNING_MAN_FILE), "a+", encoding="utf-8") as f:
        if hasattr(item, "execution_count"):
            if report is None:
                raise ValueError
            f.write(f"{item.nodeid}-{item.execution_count}-{str(report.outcome)}\n")
        else:
            f.write(f"{item.nodeid}\n")


def read_testcase_running_status(item, reruns=None):
    """
    read testcase running status
    :param item: pytest item object
    :return:
    """
    running_man_file = os.path.expanduser(setting.RUNNING_MAN_FILE)
    if os.path.exists(running_man_file):
        with open(running_man_file, "r", encoding="utf-8") as f:
            marks = f.readlines()
        if reruns:
            for i in range(reruns + 1):
                nodeid_pass = f"{item.nodeid}-{i + 1}-passed\n"
                if nodeid_pass in marks:
                    # 如果其中有一次是passed，说明已经执行完了，返回True
                    return True
            nodeid_fail = f"{item.nodeid}-{reruns + 1}-failed\n"
            if nodeid_fail in marks:
                # 如果第最后一次执行已经失败了，说明已经执行完了，返回True
                return True
            # 其他情况返回False
            return False
        else:
            nodeid = f"{item.nodeid}\n"
            if nodeid in marks:
                # already executed
                return True
    # not executed
    return False
