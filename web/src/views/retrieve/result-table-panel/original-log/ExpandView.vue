<!--
  - Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
  - Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
  - BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
  -
  - License for BK-LOG 蓝鲸日志平台:
  - -------------------------------------------------------------------
  -
  - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
  - documentation files (the "Software"), to deal in the Software without restriction, including without limitation
  - the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
  - and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
  - The above copyright notice and this permission notice shall be included in all copies or substantial
  - portions of the Software.
  -
  - THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
  - LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
  - NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
  - WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  - SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
  -->

<template>
  <div class="expand-view-wrapper">
    <div class="view-tab">
      <span
        :class="{ 'active': activeExpandView === 'kv' }"
        @click="activeExpandView = 'kv'">
        KV
      </span>
      <span
        :class="{ 'active': activeExpandView === 'json' }"
        @click="activeExpandView = 'json'">
        JSON
      </span>
    </div>
    <div class="view-content kv-view-content" v-show="activeExpandView === 'kv'">
      <kv-list
        v-bind="$attrs"
        :data="data"
        :field-list="totalFields"
        :total-fields="totalFields"
        @menuClick="(val) => $emit('menuClick', val)">
      </kv-list>
    </div>
    <div class="view-content json-view-content" v-show="activeExpandView === 'json'">
      <VueJsonPretty :deep="5" :data="data" />
    </div>
  </div>
</template>

<script>
import KvList from '../../result-comp/KvList.vue';

export default {
  components: {
    KvList,
  },
  props: {
    data: {
      type: Object,
      default: () => {},
    },
    totalFields: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      activeExpandView: 'kv',
    };
  },
};
</script>

<style lang="scss" scoped>
.expand-view-wrapper {
  .view-tab {
    font-size: 0;
    background-color: #FAFBFD;
    span {
      display: inline-block;
      width: 68px;
      height: 26px;
      line-height: 26px;
      font-size: 12px;
      border: 1px solid #eaebf0;
      background-color: #F5F7FA;
      border-top: 0;
      text-align: center;
      cursor: pointer;
      &:first-child {
        border-left: 0;
      }
      &.active {
        border: 0;
        color: #3a84ff;
        background-color: #FAFBFD;
      }
    }
  }
  .view-content {
    padding: 10px 30px;
    background-color: #FAFBFD;
    /deep/ .vjs-tree {
      font-size: 12px !important;
      .vjs-value__string {
        white-space: pre-wrap;
        tab-size: 3;
      }
    }
  }
}
</style>
