# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
License for BK-LOG 蓝鲸日志平台:
--------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from django.utils.translation import ugettext_lazy as _

from apps.exceptions import BaseException, ErrorCode


# =================================================
# 日志聚类模块
# =================================================


class BaseClusteringException(BaseException):
    MODULE_CODE = ErrorCode.BKLOG_CLUSTERING
    MESSAGE = _("日志聚类模块异常")


class ClusteringClosedException(BaseClusteringException):
    ERROR_CODE = "001"
    MESSAGE = _("聚类未开放")


class NodeConfigException(BaseClusteringException):
    ERROR_CODE = "002"
    MESSAGE = _("获取node config异常{steps}")


class NotSupportStepNameQueryException(BaseClusteringException):
    ERROR_CODE = "003"
    MESSAGE = _("不支持的step_name状态获取: {step_name}")


class EvaluationStatusResponseException(BaseClusteringException):
    ERROR_CODE = "004"
    MESSAGE = _("evaluation_status返回异常: {evaluation_status}")


class ClusteringConfigNotExistException(BaseClusteringException):
    ERROR_CODE = "005"
    MESSAGE = _("聚类配置不存在")
