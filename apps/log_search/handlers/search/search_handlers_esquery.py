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
import json
import copy
import hashlib

from typing import List, Dict, Any, Union
from django.core.cache import cache
from django.conf import settings
from requests.exceptions import ReadTimeout

from apps.api.base import DataApiRetryClass
from apps.log_clustering.models import ClusteringConfig
from apps.log_databus.constants import EtlConfig, TargetNodeTypeEnum
from apps.log_databus.models import CollectorConfig
from apps.log_search.models import (
    LogIndexSet,
    LogIndexSetData,
    Scenario,
    UserIndexSetConfig,
    UserIndexSetSearchHistory,
)
from apps.log_search.constants import (
    TimeEnum,
    SCROLL,
    MAX_RESULT_WINDOW,
    MAX_SEARCH_SIZE,
    BK_BCS_APP_CODE,
    ASYNC_SORTED,
    FieldDataTypeEnum,
    MAX_EXPORT_REQUEST_RETRY,
    DEFAULT_BK_CLOUD_ID,
)
from apps.log_search.exceptions import (
    BaseSearchIndexSetException,
    BaseSearchIndexSetDataDoseNotExists,
    BaseSearchResultAnalyzeException,
    BaseSearchGseIndexNoneException,
    BaseSearchSortListException,
    SearchExceedMaxSizeException,
    SearchUnKnowTimeFieldType,
    SearchIndexNoTimeFieldException,
    SearchNotTimeFieldType,
)

from apps.feature_toggle.handlers.toggle import FeatureToggleObject
from apps.api import BkLogApi, PaasCcApi
from apps.utils.cache import cache_five_minute
from apps.utils.db import array_group
from apps.utils.local import get_request_username
from apps.log_search.handlers.es.dsl_bkdata_builder import (
    DslBkDataCreateSearchContextBody,
    DslBkDataCreateSearchContextBodyScenarioLog,
    DslBkDataCreateSearchTailBody,
    DslBkDataCreateSearchTailBodyScenarioLog,
)
from apps.log_search.handlers.es.indices_optimizer_context_tail import IndicesOptimizerContextTail
from apps.utils.local import get_local_param
from apps.log_search.handlers.biz import BizHandler
from apps.log_search.handlers.search.mapping_handlers import MappingHandlers
from apps.log_search.handlers.search.search_sort_builder import SearchSortBuilder
from apps.log_search.handlers.search.pre_search_handlers import PreSearchHandlers
from apps.log_search.constants import TimeFieldTypeEnum, TimeFieldUnitEnum

max_len_dict = Dict[str, int]


def fields_config(name: str, is_active: bool = False):
    def decorator(func):
        def func_decorator(*args, **kwargs):
            config = {"name": name, "is_active": is_active}
            result = func(*args, **kwargs)
            if isinstance(result, tuple):
                config["is_active"], config["extra"] = result
                return config
            if result is None:
                return config
            config["is_active"] = result
            return config

        return func_decorator

    return decorator


class SearchHandler(object):
    def __init__(self, index_set_id: int, search_dict: dict, pre_check_enable=True, can_highlight=True):
        self.search_dict: dict = search_dict

        # 透传查询类型
        self.index_set_id = index_set_id
        self.search_dict.update({"index_set_id": index_set_id})

        self.scenario_id: str = ""
        self.storage_cluster_id: int = -1

        # 构建索引集字符串, 并初始化scenario_id、storage_cluster_id
        self.indices: str = self._init_indices_str(index_set_id)
        self.search_dict.update(
            {"indices": self.indices, "scenario_id": self.scenario_id, "storage_cluster_id": self.storage_cluster_id}
        )

        # 拥有以上信息后可以进行初始化检查
        # 添加是否强校验的开关来控制是否强校验
        if pre_check_enable:
            self.search_dict.update(
                PreSearchHandlers.pre_check_fields(self.indices, self.scenario_id, self.storage_cluster_id)
            )

        # 检索历史记录
        self.addition = copy.deepcopy(search_dict.get("addition", []))
        self.host_scopes = copy.deepcopy(search_dict.get("host_scopes", {}))

        self.use_time_range = search_dict.get("use_time_range", True)
        # 构建时间字段
        self.time_field, self.time_field_type, self.time_field_unit = self._init_time_field(
            index_set_id, self.scenario_id
        )
        if not self.time_field:
            raise SearchIndexNoTimeFieldException()
        self.search_dict.update(
            {
                "time_field": self.time_field,
                "time_field_type": self.time_field_type,
                "time_field_unit": self.time_field_unit,
            }
        )
        # 根据时间字段确定时间字段类型，根据预查询强校验es拉取到的时间类型
        # 添加是否强校验的开关来控制是否强校验
        if pre_check_enable:
            self.time_field_type = self._set_time_filed_type(
                self.time_field, self.search_dict.get("fields_from_es", [])
            )
        self.search_dict.update({"time_field_type": self.time_field_type})

        # 设置IP字段对应的field ip serverIp
        self.ip_field: str = "ip" if self.scenario_id in [Scenario.BKDATA, Scenario.ES] else "serverIp"

        # 上下文、实时日志传递查询类型
        self.search_type_tag: str = search_dict.get("search_type_tag")

        # 透传时间
        self.time_range: str = search_dict.get("time_range")
        self.start_time: str = search_dict.get("start_time")
        self.end_time: str = search_dict.get("end_time")
        self.time_zone: str = get_local_param("time_zone")

        # 透传query string
        self.query_string: str = search_dict.get("keyword")

        # 透传start
        self.start: int = search_dict.get("begin", 0)

        # 透传size
        self.size: int = search_dict.get("size", 30)

        # 透传filter
        self.filter: list = self._init_filter()

        # 构建排序list
        self.sort_list: list = self._init_sort()

        # 构建aggs 聚合
        self.aggs: dict = self._init_aggs()

        # 初始化highlight
        self.highlight: dict = self._init_highlight(can_highlight)

        # result fields
        self.field: Dict[str, max_len_dict] = {}

        # scroll 分页查询
        self.is_scroll: bool = settings.FEATURE_EXPORT_SCROLL

        # scroll
        self.scroll = SCROLL if self.is_scroll else None

        # collapse
        self.collapse = self.search_dict.get("collapse")

        # context search
        self.gseindex: int = search_dict.get("gseindex")
        self.gseIndex: int = search_dict.get("gseIndex")
        self.serverIp: str = search_dict.get("serverIp")
        self.ip: str = search_dict.get("ip", "undefined")
        self.path: str = search_dict.get("path", "")
        self.container_id: str = search_dict.get("container_id", None)
        self.logfile: str = search_dict.get("logfile", None)
        self._iteration_idx: str = search_dict.get("_iteration_idx", None)
        self.iterationIdx: str = search_dict.get("iterationIdx", None)
        self.iterationIndex: str = search_dict.get("iterationIndex", None)
        self.dtEventTimeStamp = search_dict.get("dtEventTimeStamp", None)

        # 上下文初始化标记
        self.zero: bool = search_dict.get("zero", False)

    def fields(self, scope="default"):
        # field_result, display_fields = self._get_all_fields_by_index_id(scope)
        # sort_list: list = self._get_sort_list_by_index_id(scope)
        mapping_handlers = MappingHandlers(
            self.indices,
            self.index_set_id,
            self.scenario_id,
            self.storage_cluster_id,
            self.time_field,
            start_time=self.start_time,
            end_time=self.end_time,
        )
        field_result, display_fields = mapping_handlers.get_all_fields_by_index_id(scope)
        sort_list: list = MappingHandlers.get_sort_list_by_index_id(self.index_set_id, scope)

        # 校验sort_list字段是否存在
        field_result_list = [i["field_name"] for i in field_result]
        sort_field_list = [j for j in sort_list if j[0] in field_result_list]

        if not sort_field_list and self.scenario_id in [Scenario.BKDATA, Scenario.LOG]:
            sort_field_list = self.sort_list

        result_dict: dict = {
            "fields": field_result,
            "display_fields": display_fields,
            "sort_list": sort_field_list,
            "time_field": self.time_field,
            "time_field_type": self.time_field_type,
            "time_field_unit": self.time_field_unit,
            "config": [],
        }
        for fields_config in [
            self.bcs_web_console(field_result_list),
            self.bk_log_to_trace(),
            self.analyze_fields(field_result),
            self.bkmonitor(field_result_list),
            self.async_export(field_result),
            self.ip_topo_switch(),
            self.clustering_config(),
            self.clean_config(),
        ]:
            result_dict["config"].append(fields_config)

        return result_dict

    @fields_config("async_export")
    def async_export(self, field_result):
        result = MappingHandlers.async_export_fields(field_result, self.scenario_id)
        if result["async_export_usable"]:
            return True, {"fields": result["async_export_fields"]}
        return False, {"usable_reason": result["async_export_usable_reason"]}

    @fields_config("bkmonitor")
    def bkmonitor(self, field_result_list):
        if "ip" in field_result_list or "serverIp" in field_result_list:
            return True

    @fields_config("ip_topo_switch")
    def ip_topo_switch(self):
        return MappingHandlers.init_ip_topo_switch(self.index_set_id)

    @fields_config("clustering_config")
    def clustering_config(self):
        """
        判断聚类配置
        """
        log_index_set = LogIndexSet.objects.get(index_set_id=self.index_set_id)
        clustering_config = ClusteringConfig.objects.filter(index_set_id=self.index_set_id).first()
        if clustering_config:
            return True, {
                "collector_config_id": log_index_set.collector_config_id,
                "signature_switch": clustering_config.signature_enable,
                "clustering_field": clustering_config.clustering_fields,
            }
        return False, {"collector_config_id": None, "signature_switch": False, "clustering_field": None}

    @fields_config("clean_config")
    def clean_config(self):
        """
        获取清洗配置
        """
        log_index_set = LogIndexSet.objects.get(index_set_id=self.index_set_id)
        if not log_index_set.collector_config_id:
            return False, {"collector_config_id": None}
        collector_config = CollectorConfig.objects.get(collector_config_id=log_index_set.collector_config_id)
        return collector_config.etl_config != EtlConfig.BK_LOG_TEXT, {
            "collector_scenario_id": collector_config.collector_scenario_id,
            "collector_config_id": log_index_set.collector_config_id,
        }

    @fields_config("context_and_realtime")
    def analyze_fields(self, field_result):
        result = MappingHandlers.analyze_fields(field_result)
        if result["context_search_usable"]:
            return True, {"reason": ""}
        return False, {"reason": result["usable_reason"]}

    @fields_config("bcs_web_console")
    def bcs_web_console(self, field_result_list):
        if not self._enable_bcs_manage():
            return False
        if (
            LogIndexSet.objects.get(index_set_id=self.index_set_id).source_app_code == BK_BCS_APP_CODE
            and "cluster" in field_result_list
            and "container_id" in field_result_list
        ):
            return True
        return False

    @fields_config("trace")
    def bk_log_to_trace(self):
        """
        [{
            "log_config": [{
                "index_set_id": 111,
                "field": "span_id"
            }],
            "trace_config": {
                "index_set_name": "xxxxxx"
            }
        }]
        """
        if not FeatureToggleObject.switch("bk_log_to_trace"):
            return False
        toggle = FeatureToggleObject.toggle("bk_log_to_trace")
        feature_config = toggle.feature_config
        if isinstance(feature_config, dict):
            feature_config = [feature_config]

        if not feature_config:
            return False

        for config in feature_config:
            log_config = config.get("log_config", [])
            target_config = [c for c in log_config if str(c["index_set_id"]) == str(self.index_set_id)]
            if not target_config:
                continue
            target_config, *_ = target_config
            return True, {**config.get("trace_config"), "field": target_config["field"]}

    def search(self, search_type="default"):

        # 校验是否超出最大查询数量
        if not self.is_scroll and self.size > MAX_RESULT_WINDOW:
            self.size = MAX_RESULT_WINDOW

        if self.is_scroll and self.size > MAX_SEARCH_SIZE:
            raise SearchExceedMaxSizeException(SearchExceedMaxSizeException.MESSAGE.format(size=MAX_SEARCH_SIZE))

        # 判断size，单次最大查询10000条数据
        once_size = copy.deepcopy(self.size)
        if self.size > MAX_RESULT_WINDOW:
            once_size = MAX_RESULT_WINDOW

        result: dict = BkLogApi.search(
            {
                "indices": self.indices,
                "scenario_id": self.scenario_id,
                "storage_cluster_id": self.storage_cluster_id,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "query_string": self.query_string,
                "filter": self.filter,
                "sort_list": self.sort_list,
                "start": self.start,
                "size": once_size,
                "aggs": self.aggs,
                "highlight": self.highlight,
                "use_time_range": self.use_time_range,
                "time_zone": self.time_zone,
                "time_range": self.time_range,
                "time_field": self.time_field,
                "time_field_type": self.time_field_type,
                "time_field_unit": self.time_field_unit,
                "scroll": self.scroll,
                "collapse": self.collapse,
            }
        )

        # 需要scroll滚动查询：is_scroll为True，size超出单次最大查询限制，total大于MAX_RESULT_WINDOW
        # @TODO bkdata暂不支持scroll查询
        if self._can_scroll(result):
            result = self._scroll(result)

        result = self._deal_query_result(result)
        field_dict = self._analyze_field_length(result.get("list"))
        result.update({"fields": field_dict})

        # 保存检索历史，按用户、索引集、检索条件缓存5分钟
        # 保存首页检索和trace通用查询检索历史
        if search_type:
            self._save_history(result, search_type)
        return result

    def _save_history(self, result, search_type):
        params = {"keyword": self.query_string, "host_scopes": self.host_scopes, "addition": self.addition}
        username = get_request_username()
        self._cache_history(
            username=username, index_set_id=self.index_set_id, params=params, search_type=search_type, result=result
        )

    @cache_five_minute("search_history_{username}_{index_set_id}_{search_type}_{params}", need_md5=True)
    def _cache_history(self, *, username, index_set_id, params, search_type, result):  # noqa
        history_params = copy.deepcopy(params)
        history_params.update({"start_time": self.start_time, "end_time": self.end_time, "time_range": self.time_range})

        # 首页检索历史在decorator记录
        if search_type == "default":
            result.update(
                {
                    "history_obj": {
                        "params": history_params,
                        "index_set_id": self.index_set_id,
                        "search_type": search_type,
                    }
                }
            )
        else:
            UserIndexSetSearchHistory.objects.create(
                index_set_id=self.index_set_id, params=history_params, search_type=search_type
            )

    def _can_scroll(self, result) -> bool:
        return (
            self.scenario_id != Scenario.BKDATA
            and self.is_scroll
            and result["hits"]["total"] > MAX_RESULT_WINDOW
            and self.size > MAX_RESULT_WINDOW
        )

    def _scroll(self, search_result):

        scroll_result = copy.deepcopy(search_result)
        scroll_size = len(scroll_result["hits"]["hits"])
        result_size = len(search_result["hits"]["hits"])

        # 判断是否继续查询：scroll_result["hits"]["hits"] == 10000 & 查询doc数量不足size
        while scroll_size == MAX_RESULT_WINDOW and result_size < self.size:
            _scroll_id = scroll_result["_scroll_id"]
            scroll_result = BkLogApi.scroll(
                {
                    "indices": self.indices,
                    "scenario_id": self.scenario_id,
                    "storage_cluster_id": self.storage_cluster_id,
                    "scroll": self.scroll,
                    "scroll_id": _scroll_id,
                }
            )

            scroll_size = len(scroll_result["hits"]["hits"])
            less_size = self.size - result_size
            if less_size < scroll_size:
                search_result["hits"]["hits"].extend(scroll_result["hits"]["hits"][:less_size])
            else:
                search_result["hits"]["hits"].extend(scroll_result["hits"]["hits"])
            result_size = len(search_result["hits"]["hits"])
            search_result["hits"]["total"] = scroll_result["hits"]["total"]

        return search_result

    def pre_get_result(self, sorted_fields: list, size: int):
        if self.scenario_id == Scenario.ES:
            result = BkLogApi.search(
                {
                    "indices": self.indices,
                    "scenario_id": self.scenario_id,
                    "storage_cluster_id": self.storage_cluster_id,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "query_string": self.query_string,
                    "filter": self.filter,
                    "sort_list": self.sort_list,
                    "start": self.start,
                    "size": size,
                    "aggs": self.aggs,
                    "highlight": self.highlight,
                    "time_zone": self.time_zone,
                    "time_range": self.time_range,
                    "use_time_range": self.use_time_range,
                    "time_field": self.time_field,
                    "time_field_type": self.time_field_type,
                    "time_field_unit": self.time_field_unit,
                    "scroll": SCROLL,
                    "collapse": self.collapse,
                },
                data_api_retry_cls=DataApiRetryClass.create_retry_obj(
                    ReadTimeout,
                    stop_max_attempt_number=MAX_EXPORT_REQUEST_RETRY,
                ),
            )
            return result

        sorted_list = [[sorted_field, ASYNC_SORTED] for sorted_field in sorted_fields]

        result = BkLogApi.search(
            {
                "indices": self.indices,
                "scenario_id": self.scenario_id,
                "storage_cluster_id": self.storage_cluster_id,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "query_string": self.query_string,
                "filter": self.filter,
                "sort_list": sorted_list,
                "start": self.start,
                "size": size,
                "aggs": self.aggs,
                "highlight": self.highlight,
                "time_zone": self.time_zone,
                "time_range": self.time_range,
                "time_field": self.time_field,
                "use_time_range": self.use_time_range,
                "time_field_type": self.time_field_type,
                "time_field_unit": self.time_field_unit,
                "scroll": None,
                "collapse": self.collapse,
            },
            data_api_retry_cls=DataApiRetryClass.create_retry_obj(
                ReadTimeout, stop_max_attempt_number=MAX_EXPORT_REQUEST_RETRY
            ),
        )
        return result

    def search_after_result(self, search_result, sorted_fields):
        search_after_size = len(search_result["hits"]["hits"])
        result_size = search_after_size
        sorted_list = [[sorted_field, ASYNC_SORTED] for sorted_field in sorted_fields]
        while search_after_size == MAX_RESULT_WINDOW and result_size < self.size:
            search_after = []
            for sorted_field in sorted_fields:
                search_after.append(search_result["hits"]["hits"][-1]["_source"].get(sorted_field))
            search_result = BkLogApi.search(
                {
                    "indices": self.indices,
                    "scenario_id": self.scenario_id,
                    "storage_cluster_id": self.storage_cluster_id,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "query_string": self.query_string,
                    "filter": self.filter,
                    "sort_list": sorted_list,
                    "start": self.start,
                    "size": MAX_RESULT_WINDOW,
                    "aggs": self.aggs,
                    "highlight": self.highlight,
                    "time_zone": self.time_zone,
                    "time_range": self.time_range,
                    "use_time_range": self.use_time_range,
                    "time_field": self.time_field,
                    "time_field_type": self.time_field_type,
                    "time_field_unit": self.time_field_unit,
                    "scroll": self.scroll,
                    "collapse": self.collapse,
                    "search_after": search_after,
                },
                data_api_retry_cls=DataApiRetryClass.create_retry_obj(
                    ReadTimeout, stop_max_attempt_number=MAX_EXPORT_REQUEST_RETRY
                ),
            )

            search_after_size = len(search_result["hits"]["hits"])
            result_size += search_after_size
            yield self._deal_query_result(search_result)

    def scroll_result(self, scroll_result):
        scroll_size = len(scroll_result["hits"]["hits"])
        result_size = scroll_size
        while scroll_size == MAX_RESULT_WINDOW and result_size < self.size:
            _scroll_id = scroll_result["_scroll_id"]
            scroll_result = BkLogApi.scroll(
                {
                    "indices": self.indices,
                    "scenario_id": self.scenario_id,
                    "storage_cluster_id": self.storage_cluster_id,
                    "scroll": SCROLL,
                    "scroll_id": _scroll_id,
                },
                data_api_retry_cls=DataApiRetryClass.create_retry_obj(
                    ReadTimeout, stop_max_attempt_number=MAX_EXPORT_REQUEST_RETRY
                ),
            )
            scroll_size = len(scroll_result["hits"]["hits"])
            result_size += scroll_size
            yield self._deal_query_result(scroll_result)

    def _get_sort_list_by_index_id(self, scope="default"):
        username = get_request_username()
        index_config_obj = UserIndexSetConfig.objects.filter(
            index_set_id=self.index_set_id, created_by=username, scope=scope, is_deleted=False
        )
        if not index_config_obj.exists():
            return list()

        sort_list = index_config_obj.first().sort_list
        return sort_list if isinstance(sort_list, list) else list()

    @staticmethod
    def get_bcs_manage_url(cluster_id, container_id):

        bcs_cluster_info = PaasCcApi.get_cluster_by_cluster_id({"cluster_id": cluster_id})
        project_id = bcs_cluster_info["project_id"]
        url = (
            settings.BCS_WEB_CONSOLE_DOMAIN + "backend/web_console/projects/{project_id}/clusters/{cluster_id}/"
            "?container_id={container_id} ".format(
                project_id=project_id, cluster_id=cluster_id.upper(), container_id=container_id
            )
        )
        return url

    @staticmethod
    def _get_cache_key(basic_key, params):
        cache_str = "{basic_key}_{params}".format(basic_key=basic_key, params=json.dumps(params))
        hash_md5 = hashlib.new("md5")
        hash_md5.update(cache_str.encode("utf-8"))
        cache_key = hash_md5.hexdigest()
        return cache_key

    @staticmethod
    def search_history(index_set_id=None, **kwargs):
        username = get_request_username()
        if index_set_id:
            history_obj = (
                UserIndexSetSearchHistory.objects.filter(
                    is_deleted=False, created_by=username, index_set_id=index_set_id, search_type="default"
                )
                .order_by("-rank", "-created_at")[:10]
                .values("id", "params")
            )
        else:
            history_obj = (
                UserIndexSetSearchHistory.objects.filter(
                    is_deleted=False,
                    search_type="default",
                    created_at__range=[kwargs["start_time"], kwargs["end_time"]],
                )
                .order_by("created_by", "-created_at")
                .values("id", "params", "created_by", "created_at")
            )
        history_obj = SearchHandler._deal_repeat_history(history_obj)
        return_data = []
        for _history in history_obj:
            return_data.append(SearchHandler._build_query_string(_history))
        return return_data

    @staticmethod
    def _build_query_string(history):
        key_word = history["params"].get("keyword", "")
        if key_word is None:
            key_word = ""
        query_string = key_word
        # IP快选、过滤条件
        host_scopes = history["params"].get("host_scopes", {})

        target_nodes = host_scopes.get("target_nodes", {})

        if target_nodes:
            if host_scopes["target_node_type"] == TargetNodeTypeEnum.INSTANCE.value:
                query_string += " AND ({})".format(
                    ",".join([f"{target_node['bk_cloud_id']}:{target_node['ip']}" for target_node in target_nodes])
                )
            else:
                first_node, *_ = target_nodes
                target_list = [str(target_node["bk_inst_id"]) for target_node in target_nodes]
                query_string += f" AND ({first_node['bk_obj_id']}:" + ",".join(target_list) + ")"

        if host_scopes.get("modules"):
            modules_list = [str(_module["bk_inst_id"]) for _module in host_scopes["modules"]]
            query_string += " ADN (modules:" + ",".join(modules_list) + ")"
            host_scopes["target_node_type"] = TargetNodeTypeEnum.TOPO.value
            host_scopes["target_nodes"] = host_scopes["modules"]

        if host_scopes.get("ips"):
            query_string += " AND (ips:" + host_scopes["ips"] + ")"
            host_scopes["target_node_type"] = TargetNodeTypeEnum.INSTANCE.value
            host_scopes["target_nodes"] = [
                {"ip": ip, "bk_cloud_id": DEFAULT_BK_CLOUD_ID} for ip in host_scopes["ips"].split(",")
            ]

        additions = history["params"].get("addition", [])

        if additions:
            query_string += (
                " AND ("
                + " AND ".join(
                    [f'{addition["field"]} {addition["operator"]} {addition["value"]}' for addition in additions]
                )
                + ")"
            )
        history["query_string"] = query_string
        return history

    @staticmethod
    def _deal_repeat_history(history_obj):
        not_repeat_history: list = []

        def _eq_history(op1, op2):
            op1_params: dict = op1["params"]
            op2_params: dict = op2["params"]
            if op1_params["keyword"] != op2_params["keyword"]:
                return False
            if op1_params["addition"] != op2_params["addition"]:
                return False
            host_scopes_op1: dict = op1_params["host_scopes"]
            host_scopes_op2: dict = op2_params["host_scopes"]
            if host_scopes_op1["ips"] != host_scopes_op2["ips"]:
                return False
            if host_scopes_op1["modules"] != host_scopes_op2["modules"]:
                return False
            return True

        def _not_repeat(history):
            for _not_repeat_history in not_repeat_history:
                if _eq_history(_not_repeat_history, history):
                    return
            not_repeat_history.append(history)

        for _history_obj in history_obj:
            _not_repeat(_history_obj)
        return not_repeat_history

    @staticmethod
    def user_search_history(start_time, end_time):
        history_obj = (
            UserIndexSetSearchHistory.objects.filter(
                is_deleted=False,
                search_type="default",
                created_at__range=[start_time, end_time],
            )
            .order_by("created_by", "-created_at")
            .values("id", "index_set_id", "duration", "created_by", "created_at")
        )

        # 获取索引集所在的bk_biz_id
        index_sets = array_group(LogIndexSet.get_index_set(show_indices=False), "index_set_id", group=True)
        return_data = []
        for _history in history_obj:
            if _history["index_set_id"] not in index_sets:
                continue
            _history["bk_biz_id"] = index_sets[_history["index_set_id"]]["bk_biz_id"]
            return_data.append(_history)
        return return_data

    def verify_sort_list_item(self, sort_list):
        # field_result, _ = self._get_all_fields_by_index_id()
        mapping_handlers = MappingHandlers(
            self.indices, self.index_set_id, self.scenario_id, self.storage_cluster_id, self.time_field
        )
        field_result, _ = mapping_handlers.get_all_fields_by_index_id()
        field_dict = dict()
        for _field in field_result:
            field_dict[_field["field_name"]] = _field["es_doc_values"]

        for _item in sort_list:
            field, *_ = _item
            item_doc_value = field_dict.get(field)
            if not item_doc_value:
                raise BaseSearchSortListException(BaseSearchSortListException.MESSAGE.format(sort_item=field))

    def search_context(self):
        if self.scenario_id not in [Scenario.BKDATA, Scenario.LOG]:
            return {"total": 0, "took": 0, "list": []}
        if not self.gseindex and not self.gseIndex:
            raise BaseSearchGseIndexNoneException()

        context_indice = IndicesOptimizerContextTail(
            self.indices, self.scenario_id, dtEventTimeStamp=self.dtEventTimeStamp, search_type_tag="context"
        ).index

        if self.zero:
            # up
            body: dict = self._get_context_body("-")
            result_up: dict = BkLogApi.dsl({"indices": context_indice, "scenario_id": self.scenario_id, "body": body})
            result_up: dict = self._deal_query_result(result_up)
            result_up.update(
                {
                    "list": list(reversed(result_up.get("list"))),
                    "origin_log_list": list(reversed(result_up.get("origin_log_list"))),
                }
            )

            # down
            body: dict = self._get_context_body("+")

            result_down: Dict = BkLogApi.dsl({"indices": context_indice, "scenario_id": self.scenario_id, "body": body})

            result_down: dict = self._deal_query_result(result_down)
            result_down.update(
                # self.analyze_context_result(result_down.get("list"))
                {"list": result_down.get("list"), "origin_log_list": result_down.get("origin_log_list")}
            )
            total = result_up["total"] + result_down["total"]
            took = result_up["took"] + result_down["took"]
            new_list = result_up["list"] + result_down["list"]
            origin_log_list = result_up["origin_log_list"] + result_down["origin_log_list"]
            analyze_result_dict: dict = self._analyze_context_result(
                new_list, mark_gseindex=self.gseindex, mark_gseIndex=self.gseIndex
            )
            zero_index: int = analyze_result_dict.get("zero_index", -1)
            count_start: int = analyze_result_dict.get("count_start", -1)

            new_list = self._analyze_empty_log(new_list)
            origin_log_list = self._analyze_empty_log(origin_log_list)
            return {
                "total": total,
                "took": took,
                "list": new_list,
                "origin_log_list": origin_log_list,
                "zero_index": zero_index,
                "count_start": count_start,
                "dsl": json.dumps(body),
            }
        if self.start < 0:
            body: Dict = self._get_context_body("-")
            result_up = BkLogApi.dsl({"indices": context_indice, "scenario_id": self.scenario_id, "body": body})

            result_up: dict = self._deal_query_result(result_up)
            result_up.update(
                # self.analyze_context_result(result_up.get("list"))
                {
                    "list": list(reversed(result_up.get("list"))),
                    "origin_log_list": list(reversed(result_up.get("origin_log_list"))),
                }
            )
            result_up.update(
                {
                    "list": self._analyze_empty_log(result_up.get("list")),
                    "origin_log_list": self._analyze_empty_log(result_up.get("origin_log_list")),
                }
            )
            return result_up
        if self.start > 0:
            body: Dict = self._get_context_body("+")
            result_down = BkLogApi.dsl({"indices": context_indice, "scenario_id": self.scenario_id, "body": body})

            result_down = self._deal_query_result(result_down)
            result_down.update(
                # self.analyze_context_result(result_down.get("list"))
                {"list": result_down.get("list"), "origin_log_list": result_down.get("origin_log_list")}
            )
            result_down.update(
                {
                    "list": self._analyze_empty_log(result_down.get("list")),
                    "origin_log_list": self._analyze_empty_log(result_down.get("origin_log_list")),
                }
            )
            return result_down

        return {"list": []}

    def _get_context_body(self, order):
        if self.scenario_id == Scenario.BKDATA:
            return DslBkDataCreateSearchContextBody(
                size=self.size,
                start=self.start,
                gseindex=self.gseindex,
                path=self.path,
                ip=self.ip,
                container_id=self.container_id,
                logfile=self.logfile,
                order=order,
                sort_list=["dtEventTimeStamp", "gseindex", "_iteration_idx"],
            ).body

        if self.scenario_id == Scenario.LOG:
            return DslBkDataCreateSearchContextBodyScenarioLog(
                size=self.size,
                start=self.start,
                gseIndex=self.gseIndex,
                path=self.path,
                serverIp=self.serverIp,
                container_id=self.container_id,
                logfile=self.logfile,
                order=order,
                sort_list=["dtEventTimeStamp", "gseIndex", "iterationIndex"],
            ).body
        return {}

    def search_tail_f(self):
        tail_indice = IndicesOptimizerContextTail(
            self.indices, self.scenario_id, dtEventTimeStamp=self.dtEventTimeStamp, search_type_tag="tail"
        ).index
        if self.scenario_id not in [Scenario.BKDATA, Scenario.LOG]:
            return {"total": 0, "took": 0, "list": []}
        else:
            body: Dict = {}
            if self.scenario_id == Scenario.BKDATA:
                body: Dict = DslBkDataCreateSearchTailBody(
                    sort_list=["dtEventTimeStamp", "gseindex", "_iteration_idx"],
                    size=self.size,
                    start=self.start,
                    gseindex=self.gseindex,
                    path=self.path,
                    ip=self.ip,
                    container_id=self.container_id,
                    logfile=self.logfile,
                    zero=self.zero,
                ).body
            if self.scenario_id == Scenario.LOG:
                body: Dict = DslBkDataCreateSearchTailBodyScenarioLog(
                    sort_list=["dtEventTimeStamp", "gseIndex", "iterationIndex"],
                    size=self.size,
                    start=self.start,
                    gseIndex=self.gseIndex,
                    path=self.path,
                    serverIp=self.serverIp,
                    container_id=self.container_id,
                    logfile=self.logfile,
                    zero=self.zero,
                ).body
            result = BkLogApi.dsl({"indices": tail_indice, "scenario_id": self.scenario_id, "body": body})

            result: dict = self._deal_query_result(result)
            if self.zero:
                result.update(
                    {
                        "list": list(reversed(result.get("list"))),
                        "origin_log_list": list(reversed(result.get("origin_log_list"))),
                    }
                )
            result.update(
                {
                    "list": self._analyze_empty_log(result.get("list")),
                    "origin_log_list": self._analyze_empty_log(result.get("origin_log_list")),
                }
            )
            return result

    def _init_indices_str(self, index_set_id: int) -> str:
        tmp_index_obj: LogIndexSet = LogIndexSet.objects.filter(index_set_id=index_set_id).first()
        if tmp_index_obj:
            self.scenario_id = tmp_index_obj.scenario_id
            self.storage_cluster_id = tmp_index_obj.storage_cluster_id
            index_set_data_obj_list: list = tmp_index_obj.get_indexes(has_applied=True)
            if len(index_set_data_obj_list) > 0:
                index_list: list = [x.get("result_table_id", None) for x in index_set_data_obj_list]
                return ",".join(index_list)
            raise BaseSearchIndexSetDataDoseNotExists(
                BaseSearchIndexSetDataDoseNotExists.MESSAGE.format(
                    index_set_id=str(index_set_id) + "_" + tmp_index_obj.index_set_name
                )
            )
        raise BaseSearchIndexSetException(BaseSearchIndexSetException.MESSAGE.format(index_set_id=index_set_id))

    def _init_time_field(self, index_set_id: int, scenario_id: str) -> tuple:
        # get timestamp field
        if scenario_id in [Scenario.BKDATA, Scenario.LOG]:
            return "dtEventTimeStamp", TimeFieldTypeEnum.DATE.value, TimeFieldUnitEnum.SECOND.value
        else:
            log_index_set_obj = LogIndexSet.objects.filter(index_set_id=index_set_id).first()
            time_field = log_index_set_obj.time_field
            time_field_type = log_index_set_obj.time_field_type
            time_field_unit = log_index_set_obj.time_field_unit
            if time_field:
                return time_field, time_field_type, time_field_unit
            index_set_obj: LogIndexSetData = LogIndexSetData.objects.filter(index_set_id=index_set_id).first()
            if not index_set_obj:
                raise BaseSearchIndexSetException(BaseSearchIndexSetException.MESSAGE.format(index_set_id=index_set_id))
            time_field = index_set_obj.time_field
            return time_field, TimeFieldTypeEnum.DATE.value, TimeFieldUnitEnum.SECOND.value

    def _init_sort(self) -> list:
        sort_list = SearchSortBuilder.sort_list(**self.search_dict)
        return sort_list

    # 过滤filter
    def _init_filter(self):

        new_attrs: dict = self._combine_addition_host_scope(self.search_dict)
        mapping_handlers = MappingHandlers(
            index_set_id=self.index_set_id,
            indices=self.indices,
            scenario_id=self.scenario_id,
            storage_cluster_id=self.storage_cluster_id,
        )
        filter_list: list = new_attrs.get("addition", [])
        new_filter_list: list = []
        for item in filter_list:
            field: str = item.get("key") if item.get("key") else item.get("field")
            _type = "field"
            if mapping_handlers.is_nested_field(field):
                _type = FieldDataTypeEnum.NESTED.value
            value = item.get("value")
            operator: str = item.get("method") if item.get("method") else item.get("operator")
            condition: str = item.get("condition", "and")
            if operator in ["exists", "does not exists"]:
                new_filter_list.append(
                    {"field": field, "value": "0", "operator": operator, "condition": condition, "type": _type}
                )

            # 此处对于前端传递filter为空字符串需要放行
            if (not field or not value or not operator) and not isinstance(value, str):
                continue

            new_filter_list.append(
                {"field": field, "value": value, "operator": operator, "condition": condition, "type": _type}
            )

        return new_filter_list

    # 需要esquery提供mapping接口
    def _get_filed_set_default_sort_tag(self) -> bool:
        result_table_id_list: list = self.indices.split(",")
        if len(result_table_id_list) <= 0:
            default_sort_tag: bool = False
            return default_sort_tag
        result_table_id, *_ = result_table_id_list
        # default_sort_tag: bool = False
        # get fields from cache
        fields_from_cache: str = cache.get(result_table_id)
        if not fields_from_cache:
            mapping_from_es: list = BkLogApi.mapping(
                {
                    "indices": result_table_id,
                    "scenario_id": self.scenario_id,
                    "storage_cluster_id": self.storage_cluster_id,
                }
            )
            property_dict: dict = MappingHandlers.find_property_dict_first(mapping_from_es)
            fields_result: list = MappingHandlers.get_all_index_fields_by_mapping(property_dict)
            fields_from_es: list = [
                {
                    "field_type": field["field_type"],
                    "field": field["field_name"],
                    "field_alias": field.get("field_alias"),
                    "is_display": False,
                    "is_editable": True,
                    "tag": field.get("tag", "metric"),
                    "es_doc_values": field.get("es_doc_values", False),
                }
                for field in fields_result
            ]
            if not fields_from_es:
                default_sort_tag: bool = False
                return default_sort_tag

            cache.set(result_table_id, json.dumps({"data": fields_from_es}), TimeEnum.ONE_DAY_SECOND.value)
            fields: list = fields_from_es
            fields_list: list = [x["field"] for x in fields]
            if ("gseindex" in fields_list and "_iteration_idx" in fields_list) or (
                "gseIndex" in fields_list and "iterationIndex" in fields_list
            ):
                default_sort_tag: bool = True
                return default_sort_tag
            default_sort_tag: bool = False
            return default_sort_tag

        fields_from_cache_dict: Dict[str, dict] = json.loads(fields_from_cache)
        fields: list = fields_from_cache_dict.get("data", list())
        fields_list: list = [x["field"] for x in fields]
        if ("gseindex" in fields_list and "_iteration_idx" in fields_list) or (
            "gseIndex" in fields_list and "iterationIndex" in fields_list
        ):
            default_sort_tag: bool = True
            return default_sort_tag
        default_sort_tag: bool = False
        return default_sort_tag

    def _init_aggs(self):
        if not self.search_dict.get("aggs"):
            return {}

        # 存在聚合参数，且时间聚合更新默认设置
        aggs_dict = self.search_dict["aggs"]
        return aggs_dict

    def _init_highlight(self, can_highlight=True):
        if not can_highlight:
            return {}
        # 避免多字段高亮
        if self.query_string and ":" in self.query_string:
            require_field_match = True
        else:
            require_field_match = False

        if self.scenario_id == Scenario.BKDATA:
            highlight = {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "log": {
                        # "type": "fvh"
                        "number_of_fragments": 0
                    }
                },
                "require_field_match": require_field_match,
            }
            if self.query_string == "":
                highlight = {}
            return highlight
        highlight = {
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "fields": {"*": {"number_of_fragments": 0}},
            "require_field_match": require_field_match,
        }
        return highlight

    def _deal_query_result(self, result_dict: dict) -> dict:
        result: dict = {
            "aggregations": result_dict.get("aggregations", {}),
        }
        # 将_shards 字段返回以供saas判断错误
        _shards = result_dict.get("_shards", {})
        result.update({"_shards": _shards})
        log_list: list = []
        agg_result: dict = {}
        origin_log_list: list = []
        if not result_dict.get("hits", {}).get("total"):
            result.update(
                {"total": 0, "took": 0, "list": log_list, "aggs": agg_result, "origin_log_list": origin_log_list}
            )
            return result
        # hit data
        for hit in result_dict["hits"]["hits"]:
            log = hit["_source"]
            origin_log = copy.deepcopy(log)
            origin_log_list.append(origin_log)
            _index = hit["_index"]
            log.update({"index": _index})
            if "highlight" not in hit:
                log_list.append(log)
                continue
            for key in hit["highlight"]:
                log[key] = "".join(hit["highlight"][key])
            log_list.append(log)

        result.update(
            {
                "total": result_dict["hits"]["total"],
                "took": result_dict["took"],
                "list": log_list,
                "origin_log_list": origin_log_list,
            }
        )
        # 处理聚合
        agg_dict = result_dict.get("aggregations", {})
        result.update({"aggs": agg_dict})
        return result

    def _analyze_field_length(self, log_list: List[Dict[str, Any]]):
        for item in log_list:

            def get_filed_and_get_length(_item: dict, father: str = ""):
                for key in _item:
                    _key: str = ""
                    if isinstance(_item[key], dict):
                        get_filed_and_get_length(_item[key], key)
                    else:
                        if father:
                            _key = "{}.{}".format(father, key)
                        else:
                            _key = "%s" % key
                    if _key:
                        self._update_result_fields(_key, _item[key])

            get_filed_and_get_length(item)
        return self.field

    def _update_result_fields(self, _key: str, _item: Any):
        max_len_dict_obj: max_len_dict = self.field.get(_key)
        if max_len_dict_obj:
            # modify
            _len: int = max_len_dict_obj.get("max_length")
            try:
                new_len: int = len(str(_item))
            except BaseSearchResultAnalyzeException:
                new_len: int = 16
            if new_len >= _len:
                if new_len > len(_key):
                    max_len_dict_obj.update({"max_length": new_len})
                else:
                    max_len_dict_obj.update({"max_length": len(_key)})
            return
        # insert
        try:
            new_len: int = len(str(_item))
        except BaseSearchResultAnalyzeException:
            new_len: int = 16

        if new_len > len(_key):
            self.field.update({_key: {"max_length": new_len}})
        else:
            self.field.update({_key: {"max_length": len(_key)}})

    def _analyze_context_result(
        self, log_list: List[Dict[str, Any]], mark_gseindex: int = None, mark_gseIndex: int = None
    ) -> Dict[str, Any]:

        log_list_reversed: list = log_list
        if self.start < 0:
            log_list_reversed = list(reversed(log_list))

        # find the search one
        _index: int = -1
        _count_start: int = -1
        if self.scenario_id == Scenario.BKDATA:
            for index, item in enumerate(log_list):
                gseindex: str = item.get("gseindex")
                ip: str = item.get("ip")
                path: str = item.get("path")
                container_id: str = item.get("container_id")
                logfile: str = item.get("logfile")
                _iteration_idx: str = item.get("_iteration_idx")
                # find the counting range point
                if _count_start == -1:
                    if str(gseindex) == mark_gseindex:
                        _count_start = index

                if (
                    self.gseindex == str(gseindex)
                    and self.ip == ip
                    and self.path == path
                    and self._iteration_idx == str(_iteration_idx)
                ) or (
                    self.gseindex == str(gseindex)
                    and self.container_id == container_id
                    and self.logfile == logfile
                    and self._iteration_idx == str(_iteration_idx)
                ):
                    _index = index
                    break

        if self.scenario_id == Scenario.LOG:
            for index, item in enumerate(log_list):
                gseIndex: str = item.get("gseIndex")
                serverIp: str = item.get("serverIp")
                path: str = item.get("path")
                iterationIndex: str = item.get("iterationIndex")
                # find the counting range point
                if _count_start == -1:
                    if str(gseIndex) == mark_gseIndex:
                        _count_start = index
                if (
                    self.gseIndex == str(gseIndex)
                    and self.serverIp == serverIp
                    and self.path == path
                    and self.iterationIndex == str(iterationIndex)
                ):
                    _index = index
                    break
        return {"list": log_list_reversed, "zero_index": _index, "count_start": _count_start}

    def _analyze_empty_log(self, log_list: List[Dict[str, Any]]):
        log_not_empty_list: List[Dict[str, Any]] = []
        for item in log_list:
            a_item_dict: Dict[str:Any] = item

            # 只要存在log字段则直接显示
            if "log" in a_item_dict:
                log_not_empty_list.append(a_item_dict)
                continue
            # 递归打平每条记录
            new_log_context_list: List[str] = []

            def get_field_and_get_context(_item: dict, fater: str = ""):
                for key in _item:
                    _key: str = ""
                    if isinstance(_item[key], dict):
                        get_field_and_get_context(_item[key], key)
                    else:
                        if fater:
                            _key = "{}.{}".format(fater, key)
                        else:
                            _key = "%s" % key
                    if _key:
                        a_context: str = "{}: {}".format(_key, _item[key])
                        new_log_context_list.append(a_context)

            get_field_and_get_context(a_item_dict)
            a_item_dict.update({"log": " ".join(new_log_context_list)})
            log_not_empty_list.append(a_item_dict)
        return log_not_empty_list

    def _get_addition_host(self, bk_biz_id, target_node_type: str, target_nodes: list) -> list:
        if target_node_type == TargetNodeTypeEnum.INSTANCE.value:
            return target_nodes
        conditions = [
            {"bk_obj_id": node_obj["bk_obj_id"], "bk_inst_id": node_obj["bk_inst_id"]} for node_obj in target_nodes
        ]
        host_result = BizHandler(bk_biz_id).search_host(conditions)
        return [{"ip": host["bk_host_innerip"], "bk_cloud_id": host["bk_cloud_id"]} for host in host_result]

    def _combine_addition_host_scope(self, attrs: dict):
        host_scopes_ip_list: list = []
        ips_list: list = []
        translated_ips: list = []
        target_ips = []
        host_scopes: dict = attrs.get("host_scopes")
        if host_scopes:
            modules: list = host_scopes.get("modules")
            target_nodes = host_scopes.get("target_nodes", {})
            target_node_type = host_scopes.get("target_node_type", "")
            if target_nodes:
                target_ips = [
                    host["ip"] for host in self._get_addition_host(attrs["bk_biz_id"], target_node_type, target_nodes)
                ]
            if modules:
                biz_handler = BizHandler(attrs["bk_biz_id"])
                search_list: list = biz_handler.search_host(modules)
                host_list: list = [x.get("bk_host_innerip") for x in search_list]
                translated_ips: list = host_list

            ips: str = host_scopes.get("ips")
            if ips:
                ips_list = ips.split(",")

        host_scopes_ip_list = host_scopes_ip_list + ips_list + translated_ips + target_ips
        addition_ip_list, new_addition = self._deal_addition(attrs)

        if addition_ip_list:
            search_ip_list = addition_ip_list
        elif not addition_ip_list and host_scopes_ip_list:
            search_ip_list = host_scopes_ip_list
        else:
            search_ip_list = []
        new_addition.append({"field": self.ip_field, "operator": "is one of", "value": list(set(search_ip_list))})
        attrs["addition"] = new_addition
        return attrs

    def _deal_addition(self, attrs):
        addition_ip_list: list = []
        addition: list = attrs.get("addition")
        new_addition: list = []
        if not addition:
            return [], []
        for _add in addition:
            field: str = _add.get("key") if _add.get("key") else _add.get("field")
            _operator: str = _add.get("method") if _add.get("method") else _add.get("operator")
            if field == self.ip_field:
                value = _add.get("value")
                if value and _operator in ["is", "is one of", "eq"]:
                    if isinstance(value, str):
                        addition_ip_list.extend(value.split(","))
                    elif isinstance(value, list):
                        addition_ip_list = addition_ip_list + value
                # 非IP合并的逻辑按照正常filter处理
                value = _add.get("value")
                new_value: list = []
                if value:
                    new_value = self._deal_normal_addition(value, _operator)
                new_addition.append(
                    {
                        "field": field,
                        "operator": _operator,
                        "value": new_value,
                        "condition": _add.get("condition", "and"),
                    }
                )
            # 处理逗号分隔in类型查询
            value = _add.get("value")
            new_value: list = []
            # 对于前端传递为空字符串的场景需要放行过去
            if isinstance(value, str) or value:
                new_value = self._deal_normal_addition(value, _operator)
            new_addition.append(
                {
                    "field": field,
                    "operator": _operator,
                    "value": new_value,
                    "condition": _add.get("condition", "and"),
                }
            )
        return addition_ip_list, new_addition

    def _deal_normal_addition(self, value, _operator: str) -> Union[str, list]:
        operator = _operator
        addition_return_value = {
            "is": lambda: value,
            "is one of": lambda: value.split(","),
            "is not": lambda: value,
            "is not one of": lambda: value.split(","),
        }
        return addition_return_value.get(operator, lambda: value)()

    def _set_time_filed_type(self, time_field: str, fields_from_es: list):
        if not fields_from_es:
            raise SearchNotTimeFieldType()

        for item in fields_from_es:
            field_name = item["field_name"]
            if field_name == time_field:
                return item["field_type"]
        raise SearchUnKnowTimeFieldType()

    def _enable_bcs_manage(self):
        return settings.PAASCC_APIGATEWAY if settings.PAASCC_APIGATEWAY != "" else None
