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
  <bk-table
    ref="resultTable"
    :class="['king-table', { 'is-wrap': isWrap }]"
    :data="tableList"
    :key="tableRandomKey"
    :empty-text="$t('retrieve.notData')"
    :show-header="!tableLoading"
    @row-click="tableRowClick"
    @row-mouse-enter="handleMouseEnter"
    @row-mouse-leave="handleMouseLeave"
    @header-dragend="handleHeaderDragend">
    <!-- 展开详情 -->
    <bk-table-column
      type="expand"
      width="30"
      align="center"
      v-if="visibleFields.length">
      <template slot-scope="{ $index }">
        <expand-view
          v-bind="$attrs"
          :data="originTableList[$index]"
          :total-fields="totalFields"
          :visible-fields="visibleFields"
          @menuClick="handleMenuClick">
        </expand-view>
      </template>
    </bk-table-column>
    <!-- 显示字段 -->
    <template v-for="(field, index) in visibleFields">
      <bk-table-column
        align="left"
        :key="field.field_name"
        :min-width="field.minWidth"
        :render-header="renderHeaderAliasName"
        :index="index"
        :width="field.width"
        :class-name="`visiable-field${isWrap ? ' is-wrap' : ''}`">
        <!-- eslint-disable-next-line -->
        <template slot-scope="{ row, column, $index }">
          <keep-alive>
            <div :class="['str-content', { 'is-limit': !cacheExpandStr.includes($index) }]">
              <TableColumn
                :is-wrap="isWrap"
                :content="tableRowDeepView(row, field.field_name, field.field_type)"
                :field-type="field.field_type"
                @iconClick="(type, content) => handleIconClick(type, content, field, row)"
                @computedHeight="handleOverColumn(field.field_name)"
              ></TableColumn>
              <p
                v-if="!cacheExpandStr.includes($index)"
                class="show-whole-btn"
                @click.stop="handleShowWhole($index)">
                {{ $t('展开全部') }}
              </p>
              <p
                v-else-if="cacheOverFlowCol.includes(field.field_name)"
                class="hide-whole-btn"
                @click.stop="handleHideWhole($index)">
                {{ $t('收起') }}
              </p>
            </div>
          </keep-alive>
        </template>
      </bk-table-column>
    </template>
    <!-- 操作按钮 -->
    <bk-table-column
      v-if="showHandleOption"
      :label="$t('retrieve.operate')"
      :width="84"
      align="right"
      :resizable="false">
      <!-- eslint-disable-next-line -->
      <template slot-scope="{ row, column, $index }">
        <operator-tools
          :index="$index"
          :cur-hover-index="curHoverIndex"
          :show-realtime-log="showRealtimeLog"
          :show-context-log="showContextLog"
          :show-monitor-web="showMonitorWeb"
          :show-web-console="showWebConsole"
          :handle-click="(event) => handleClickTools(event, row)">
        </operator-tools>
      </template>
    </bk-table-column>
    <!-- 初次加载骨架屏loading -->
    <bk-table-column v-if="tableLoading" slot="empty">
      <retrieve-loader
        is-loading
        :is-original-field="false"
        :visible-fields="visibleFields">
      </retrieve-loader>
    </bk-table-column>
    <!-- 下拉刷新骨架屏loading -->
    <template slot="append" v-if="tableList.length && visibleFields.length && isPageOver">
      <retrieve-loader
        :is-page-over="isPageOver"
        :is-original-field="false"
        :visible-fields="visibleFields">
      </retrieve-loader>
    </template>
  </bk-table>
</template>

<script>
import resultTableMixin from '@/mixins/resultTableMixin';

export default {
  name: 'TableList',
  mixins: [resultTableMixin],
};
</script>
