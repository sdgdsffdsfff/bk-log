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
  <div class="step-issued-wrapper"
       v-bkloading="{ isLoading: loading | (hasRunning && !tableList.length) }"
       data-test-id="addNewCollectionItem_div_collectionDistribution">
    <div class="step-issued-notice notice-primary" v-if="!curCollect.table_id">
      <i class="bk-icon icon-info-circle-shape notice-icon"></i>
      <span class="notice-text">{{ $t('dataManage.Within_stop') }}</span>
    </div>
    <template v-if="!isShowStepInfo">
      <div class="step-issued-header">
        <div class="tab-only-compact fl">
          <template v-for="(tabItem) in tabList">
            <li :class="['tab-item', { 'cur-tab': tabItem.type === curTab }]" :key="tabItem.type">
              <a
                href="javascript:void(0);"
                class="tab-button"
                @click="tabHandler(tabItem)">
                {{ `${tabItem.name}(${tabItem.num})` }}
              </a>
            </li>
          </template>
        </div>
        <bk-button
          v-if="hasFailed"
          class="fr"
          icon="refresh"
          data-test-id="collectionDistribution_button_refresh"
          :title="$t('configDetails.batchRetry')"
          :disabled="hasRunning"
          @click="issuedRetry">{{ $t('configDetails.batchRetry') }}
        </bk-button>
      </div>
      <section class="cluster-collaspse" v-if="tableList.length">
        <template v-for="cluster in tableList">
          <right-panel
            v-if="cluster.child.length"
            :class="['cluster-menu', { 'has-title-sign': cluster.is_label && isEdit }]"
            :key="cluster.id"
            :need-border="true"
            :collapse-color="'#313238'"
            :title-bg-color="'#F0F1F5'"
            :collapse.sync="cluster.collapse"
            :title="{
              type: cluster.bk_obj_name,
              number: cluster.success
            }">
            <div
              :class="`heder-title-sign sign-${cluster.label_name}`"
              v-if="cluster.is_label && isEdit"
              slot="pre-panel">
              {{ cluster.label_name === 'add' ?
                $t('dataManage.add_btn') :
                (cluster.label_name === 'modify' ?
                  $t('dataManage.amend') : $t('btn.delete')) }}
            </div>
            <div class="header-info" slot="title">
              <div class="header-title fl">{{ cluster.node_path }}</div>
              <!-- eslint-disable -->
                <p class="fl" v-html="collaspseHeadInfo(cluster)"></p>
                <!-- <span class="success">{{ cluster.success }}</span> 个成功
                <span v-if="cluster.failed" class="failed">，{{ cluster.failed }}</span> 个失败 -->
              </div>
              <!-- eslint-enabled -->
              <div class="cluster-table-wrapper" slot>
                <bk-table
                  v-bkloading="{ isLoading: loading }"
                  class="cluster-table"
                  :resizable="true"
                  :empty-text="$t('btn.vacancy')"
                  :data="cluster.child"
                  :size="size"
                  :pagination="pagination">
                  <bk-table-column :label="$t('configDetails.goal')" prop="ip" width="180"></bk-table-column>

                  <bk-table-column :label="$t('dataManage.es_host')" width="120">
                      <template slot-scope="props">
                          <span :class="['status', 'status-' + props.row.status]">
                              <i
                                class="bk-icon icon-refresh"
                                style="display: inline-block; animation: button-icon-loading 1s linear infinite;"
                                v-if="props.row.status !== 'success' && props.row.status !== 'failed'">
                              </i>
                              {{ props.row.status === 'success' ? $t('configDetails.success') : props.row.status === 'failed' ? $t('dataSource.failed') : $t('configDetails.Pending') }}
                          </span>
                      </template>
                  </bk-table-column>
                  <bk-table-column
                    :class-name="'row-detail'"
                    :label="$t('monitors.detail')">
                    <template slot-scope="props" class="row-detail">
                      <p>
                        <span style="display: inline-block">{{ props.row.log }}</span>
                        <a href="javascript: ;" class="more" @click.stop="viewDetail(props.row)">{{ $t('dataManage.more') }}</a>
                      </p>
                    </template>
                  </bk-table-column>
                  <bk-table-column width="80">
                    <template slot-scope="props">
                      <a 
                        href="javascript: ;" class="retry"
                        v-if="props.row.status === 'failed'"
                        @click.stop="issuedRetry(props.row, cluster)">
                        {{ $t('configDetails.retry') }}
                      </a>
                    </template>
                  </bk-table-column>
                </bk-table>
              </div>
            </right-panel>
          </template>
        </section>
    </template>
    <template v-else>
      <div class="empty-view">
        <i class="bk-icon icon-info-circle-shape"></i>
        <div class="hint-text">{{ $t('dataManage.StepInfo') }}</div>
      </div>
    </template>
    <div class="step-issued-footer">
      <bk-button v-if="isSwitch" theme="primary" :disabled="hasRunning" @click="nextHandler">{{ hasRunning ? $t('configDetails.Pending') : $t('dataManage.perform') }}</bk-button>
      <template v-else>
        <bk-button 
          :disabled="hasRunning" 
          @click="prevHandler"
          data-test-id="collectionDistribution_button_previous"
        >{{ $t('dataManage.last') }}</bk-button>
        <bk-button 
          theme="primary" 
          :disabled="hasRunning" 
          @click="nextHandler"
          data-test-id="collectionDistribution_button_nextStep"
        >{{ $t('dataManage.next') }}</bk-button>
      </template>
      <bk-button @click="cancel" data-test-id="collectionDistribution_button_cancel">{{ $t('dataManage.Return_list') }}</bk-button>
    </div>
    <bk-sideslider
      transfer
      :width="800"
      :quick-close="true"
      :ext-cls="'issued-detail'"
      :is-show.sync="detail.isShow"
      @animation-end="closeSlider">
      <div slot="header">{{ detail.title }}</div>
      <div class="p20 detail-content" slot="content" v-bkloading="{ isLoading: detail.loading }" v-html="detail.content"></div>
    </bk-sideslider>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import rightPanel from '@/components/ip-select/right-panel';

export default {
  name: 'step-issued',
  components: {
    rightPanel,
  },
  props: {
    operateType: String,
    isSwitch: Boolean,
  },
  data() {
    return {
      loading: true,
      notReady: false, // 节点管理准备好了吗
      detail: {
        isShow: false,
        title: this.$t('monitors.detail'),
        loading: true,
        content: '',
        log: '',
      },
      timer: null,
      timerNum: 0,
      tableListAll: [],
      tableList: [],
      curTaskIdList: new Set(),
      curTab: 'all',
      tabList: [
        {
          type: 'all',
          name: this.$t('configDetails.all'),
          num: 0,
        },
        {
          type: 'success',
          name: this.$t('configDetails.success'),
          num: 0,
        },
        {
          type: 'failed',
          name: this.$t('configDetails.failed'),
          num: 0,
        },
        {
          type: 'running',
          name: this.$t('configDetails.Pending'),
          num: 0,
        },
      ],
      count: 0,
      size: 'small',
      pagination: {
        current: 1,
        count: 0,
        limit: 100,
      },
      isShowStepInfo: false,
      // operateInfo: {}
    };
  },
  computed: {
    ...mapGetters('collect', ['curCollect']),
    hasFailed() {
      return !!this.tabList[2].num;
    },
    hasRunning() {
      return !!this.tabList[3].num || this.notReady;
    },
    isEdit() {
      return this.operateType === 'edit' || this.operateType === 'editFinish';
    },
  },
  watch: {
    hasRunning(newVal, val) {
      if (!val && newVal) {
        this.startStatusPolling();
      }
      if (!newVal) {
        this.stopStatusPolling();
      }
    },
    notReady(val) {
      if (!val) {
        const len = this.tableList.length;
        this.isShowStepInfo = this.tableList.filter(item => item.child.length === 0).length === len;
      }
    },
  },
  created() {
    this.curCollect.task_id_list.forEach(id => this.curTaskIdList.add(id));
  },
  mounted() {
    this.isShowStepInfo = false;
    this.requestIssuedClusterList();
  },
  destroyed() {
    this.stopStatusPolling();
  },
  methods: {
    tabHandler(tab, manual) {
      if (this.curTab === tab.type && !manual) {
        return false;
      }
      this.curTab = tab.type;
      if (this.curTab === 'all') {
        this.tableList = JSON.parse(JSON.stringify(this.tableListAll));
      } else {
        const child = [];
        this.tableListAll.forEach((item) => {
          const copyItem = JSON.parse(JSON.stringify(item));
          copyItem.child = copyItem.child.filter(row => row.status === this.curTab);
          if (copyItem.child.length) {
            child.push(copyItem);
          }
        });
        this.tableList.splice(0, this.tableList.length, ...child);
      }
    },
    prevHandler() {
      if (this.operateType === 'add') {
        this.$router.replace({
          name: 'collectEdit',
          params: {
            collectorId: this.curCollect.collector_config_id,
            notAdd: true,
          },
          query: {
            projectId: window.localStorage.getItem('project_id'),
          },
        });
      }
      this.$emit('stepChange', 1);
    },
    nextHandler() {
      this.$emit('stepChange');
    },
    cancel() {
      this.$router.push({
        name: 'collection-item',
        query: {
          projectId: window.localStorage.getItem('project_id'),
        },
      });
    },
    viewDetail(row) {
      this.detail.isShow = true;
      this.detail.loading = true;
      this.requestDetail(row);
    },
    closeSlider() {
      this.detail.content = '';
      this.detail.loading = false;
    },
    calcTabNum() {
      const num = {
        all: 0,
        success: 0,
        failed: 0,
        running: 0,
      };
      this.tableListAll.forEach((cluster) => {
        num.all += cluster.child.length;
        cluster.child.length && cluster.child.forEach((row) => {
          num[row.status] = num[row.status] + 1;
        });
      });
      this.tabList.forEach((tab) => {
        tab.num = num[tab.type];
      });
    },
    collaspseHeadInfo(cluster) {
      const list = cluster.child;
      let success = 0;
      let failed = 0;
      list.forEach((row) => {
        if (row.status === 'success') {
          success = success + 1;
        }
        if (row.status === 'failed') {
          failed = failed + 1;
        }
        // if (row.status === 'running') {
        //     running++
        // }
      });
      return `<span class="success">${success}</span> ${this.$t('configDetails.successful')}，<span class="failed">${failed}</span> ${this.$t('configDetails.failure')}`;
    },
    startStatusPolling() {
      this.timerNum += 1;
      this.stopStatusPolling();
      this.timer = setTimeout(() => {
        this.requestIssuedClusterList('polling');
      }, 500);
    },
    stopStatusPolling() {
      clearTimeout(this.timer);
    },
    /**
             *  集群list，与轮询共用
             */
    requestIssuedClusterList(isPolling) {
      const params = {
        collector_config_id: this.curCollect.collector_config_id,
      };
      const timerNum = this.timerNum;
      if (!isPolling) {
        this.loading = true;
      }
      this.$http.request('collect/getIssuedClusterList', {
        params,
        query: { task_id_list: [...this.curTaskIdList.keys()].join(',') },
      }).then((res) => {
        const data = res.data.contents || [];
        this.notReady = res.data.task_ready === false; // 如果没有该字段，默认准备好了
        if (isPolling === 'polling') {
          if (timerNum === this.timerNum) {
            // 之前返回的 contents 为空
            if (!this.tableListAll.length) {
              data.forEach((cluster, index) => {
                cluster.collapse = index === 0;
                cluster.child.forEach((host) => {
                  host.status = host.status === 'PENDING' ? 'running' : host.status.toLowerCase(); // pending-等待状态，与running不做区分
                });
              });
              this.tableListAll.splice(0, 0, ...data);
              this.tableList.splice(0, 0, ...data);
            }
            this.syncHostStatus(data);
            this.tabHandler({ type: this.curTab }, true);
            this.calcTabNum();
            if (this.hasRunning) {
              this.startStatusPolling();
            }
          }
        } else {
          data.forEach((cluster, index) => {
            cluster.collapse = index === 0;
            cluster.child.forEach((host) => {
              host.status = host.status === 'PENDING' ? 'running' : host.status.toLowerCase(); // pending-等待状态，与running不做区分
            });
          });
          this.tableListAll.splice(0, 0, ...data);
          this.tableList.splice(0, 0, ...data);
          this.calcTabNum();
        }
      })
        .catch((err) => {
          this.$bkMessage({
            theme: 'error',
            message: err.message,
          });
        })
        .finally(() => {
          setTimeout(() => {
            this.loading = false;
          }, 500);
        });
    },
    /**
             * 重试
             */
    issuedRetry(row, cluster) {
      const targetNodes = [];
      if (cluster) {
        // 单条重试
        row.status = 'running';
        this.tableListAll.forEach((item) => {
          if (cluster.bk_inst_id === item.bk_inst_id && cluster.bk_obj_name === item.bk_obj_name) {
            item.child && item.child.forEach((itemRow) => {
              if (itemRow.ip === row.ip && itemRow.bk_cloud_id === row.bk_cloud_id) {
                itemRow.status = 'running';
              }
            });
          }
        });
        targetNodes.push({
          ip: row.ip,
          bk_cloud_id: row.bk_cloud_id,
          bk_supplier_id: row.bk_supplier_id,
        });
      } else {
        // 失败批量重试
        this.tableListAll.forEach((item) => {
          item.child && item.child.forEach((itemRow) => {
            if (itemRow.status === 'failed') {
              itemRow.status = 'running';
              targetNodes.push({
                ip: itemRow.ip,
                bk_cloud_id: itemRow.bk_cloud_id,
                bk_supplier_id: itemRow.bk_supplier_id,
              });
            }
          });
        });
      }
      this.tabHandler({ type: this.curTab }, true);
      this.calcTabNum();
      this.$http.request('collect/retry', {
        // mock: true,
        // manualSchema: true,
        params: { collector_config_id: this.curCollect.collector_config_id },
        data: {
          target_nodes: targetNodes,
        },
      }).then((res) => {
        if (res.data) {
          res.data.forEach(item => this.curTaskIdList.add(item));
          this.startStatusPolling();
        }
      })
        .catch((err) => {
          this.$bkMessage({
            theme: 'error',
            message: err.message,
          });
        });
    },
    // 同步机器状态信息
    syncHostStatus(data) {
      this.tableListAll.forEach((table) => {
        const cluster = data.find((item) => {
          return item.bk_inst_id === table.bk_inst_id && item.bk_obj_name === table.bk_obj_name;
        });
        if (cluster && cluster.child && cluster.child.length && table.child && table.child.length) {
          table.child.forEach((row) => {
            const tarHost = cluster.child.find(item => item.bk_cloud_id === row.bk_cloud_id && item.ip === row.ip);
            if (tarHost) {
              row.status = tarHost.status === 'PENDING' ? 'running' : tarHost.status.toLowerCase(); // pending-等待状态，与running不做区分
              row.task_id = tarHost.task_id;
            }
          });
        }
      });
    },
    requestDetail(row) {
      this.$http.request('collect/executDetails', {
        params: {
          collector_id: this.curCollect.collector_config_id,
        },
        query: {
          instance_id: row.instance_id,
          task_id: row.task_id,
        },
      }).then((res) => {
        if (res.result) {
          this.detail.log = res.data.log_detail;
          this.detail.content = res.data.log_detail;
        }
      })
        .catch((err) => {
          this.$bkMessage({
            theme: 'error',
            message: err.message || err,
          });
        })
        .finally(() => {
          this.detail.loading = false;
        });
    },
  },
};
</script>

<style scoped lang="scss">
  @import '@/scss/mixins/scroller.scss';
  @import '@/scss/mixins/clearfix';
  @import '@/scss/conf';

  .step-issued-wrapper {
    position: relative;
    padding: 30px 60px;
    max-height: 100%;
    overflow-x: hidden;
    overflow-y: auto;

    .step-issued-notice {
      margin-bottom: 20px;
      padding: 9px 12px;
      height: 36px;
      line-height: 16px;
      border-radius: 2px;
      font-size: 12px;
      color: #63656e;

      .notice-text {
        margin-left: 10px;
      }

      .notice-icon {
        vertical-align: text-bottom;
        font-size: 14px;
      }

      &.notice-primary {
        border: 1px solid #a3c5fd;
        background: #f0f8ff;

        .notice-icon {
          color: #3a84ff;
        }
      }
    }

    .step-issued-header {
      margin-bottom: 20px;

      @include clearfix;
    }

    .cur-tab {
      background: #3a84ff;
    }

    .cluster-collaspse {
      max-width: 100%;
    }

    .cluster-menu {
      margin-bottom: 10px;
      max-width: 100%;

      &.has-title-sign .right-panel-title {
        padding-left: 0;
      }
    }

    .header-title {
      margin-right: 20px;
      font-weight: bold;
      color: #63656e;
    }

    .heder-title-sign {
      position: relative;
      margin-left: -1px;
      margin-right: 16px;
      padding: 0 12px 0 7px;
      height: 24px;
      line-height: 23px;
      font-size: 12px;
      color: #fff;
      background: #3a84ff;

      &.sign-add {
        background: #3a84ff;
      }

      &.sign-modify {
        background: #414871;
      }

      &.sign-delete {
        background: #6c3aff;
      }

      &:after {
        position: absolute;
        right: 0;
        top: 0;
        display: block;
        content: '';
        border-top: 12px solid transparent;
        border-bottom: 12px solid transparent;
        border-left: 6px solid transparent;
        border-right: 6px solid #f0f1f5;
      }
    }

    .header-info {
      font-size: 12px;
      color: #979ba5;

      .success {
        color: $successColor;
      }

      .failed {
        color: $failColor;
      }
    }

    .cluster-table {
      &.bk-table th :hover {
        background: #fff;
      }

      &::before {
        display: none;
      }

      tr:last-child td {
        border-bottom: none;
      }

      .status-running {
        color: $primaryColor;
      }

      .status-success {
        color: $successColor;
      }

      .status-failed {
        color: $failColor;
      }

      .retry {
        color: #3a84ff;
      }

      .row-detail {
        .more {
          display: inline;
        }

        p {
          position: relative;
          display: inline-block;
          padding-right: 30px;
          max-width: 100%;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }

      .more {
        position: absolute;
        right: 0;
        top: 0;
        color: #3a84ff;
        display: none;
      }
    }

    .step-issued-footer {
      margin-top: 20px;
    }

    .tab-only-compact {
      overflow: visible;

      @include clearfix;

      .tab-item {
        .tab-button {
          height: 32px;
          line-height: 30px;
        }

        &.cur-tab {
          .tab-button {
            color: #fff;
            background: #3a84ff;
          }
        }
      }
    }

    .step-issued-footer {
      button {
        margin-right: 10px;
      }
    }

    .empty-view {
      height: 452px;
      background: #fff;
      border-radius: 2px;
      border: 1px dashed #dcdee5;
      position: relative;
      // display: box;
      display: flexbox;
      display: flex;
      box-pack: center;
      flex-pack: center;
      justify-content: center;

      .hint-text {
        min-width: 144px;
        height: 16px;
        line-height: 16px;
        position: absolute;
        top: 186px;
        font-size: 12px;
        color: #979ba5;
      }

      .icon-info-circle-shape {
        position: absolute;
        top: 142px;
        left: calc(50% - 16px);
        font-size: 32px;
        color: #dcdee5;
      }
    }
  }

  /deep/ .bk-sideslider-wrapper {
    padding-bottom: 0;

    .bk-sideslider-content {
      background-color: #313238;
      color: #c4c6cc;
    }

    .detail-content {
      min-height: calc(100vh - 60px);
      white-space: pre-wrap;
    }
  }
</style>
