#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
class _Setting:
    # 项目名称
    PROJECT_NAME = "letmego"
    # 默认的标签记录文件的路径
    RUNNING_MAN_FILE = "/tmp/_running_man.txt"
    # 配置用例脚本的开头
    TARGET_FILE_STARTSWITH = "test"
    # 默认操作系统的密码
    PASSWORD = "1"
    # 第几次执行
    EXECUTION_COUNT = None


setting = _Setting()
