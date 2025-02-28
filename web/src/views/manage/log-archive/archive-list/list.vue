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
  <section class="log-archive-list" data-test-id="archive_section_archiveList">
    <section class="top-operation">
      <bk-button
        class="fl"
        theme="primary"
        data-test-id="archiveList_button_newArchive"
        @click="handleCreate">
        {{ $t('logArchive.archive') }}
      </bk-button>
      <div class="list-search fr">
        <bk-input
          :clearable="true"
          :right-icon="'bk-icon icon-search'"
          v-model="keyword"
          data-test-id="archiveList_input_searchListItem"
          @enter="search">
        </bk-input>
      </div>
    </section>
    <section class="log-archive-table">
      <bk-table
        class="archive-table"
        :data="dataList"
        data-test-id="archiveList_section_tableList"
        v-bkloading="{ isLoading: isTableLoading }"
        :pagination="pagination"
        :limit-list="pagination.limitList"
        @filter-change="handleFilterChange"
        @page-change="handlePageChange"
        @page-limit-change="handleLimitChange">
        <bk-table-column type="expand" width="30" align="center">
          <template slot-scope="props">
            <div class="state-table-wrapper">
              <StateTable :archive-config-id="props.row.archive_config_id" />
            </div>
          </template>
        </bk-table-column>
        <bk-table-column label="ID" width="100">
          <template slot-scope="props">
            {{ props.row.archive_config_id }}
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('logArchive.collectName')">
          <template slot-scope="props">
            {{ props.row.collector_config_name }}
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('logArchive.expired')">
          <template slot-scope="props">
            {{ `${props.row.snapshot_days}天` }}
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('logArchive.totalSize')">
          <template slot-scope="props">
            {{ getFileSize(props.row.store_size) }}
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('logArchive.indexCount')">
          <template slot-scope="props">
            {{ props.row.index_count }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="$t('logArchive.archiveRepository')"
          prop="target_snapshot_repository_name">
          <template slot-scope="props">
            {{ props.row.target_snapshot_repository_name }}
          </template>
        </bk-table-column>
        <bk-table-column :label="$t('dataSource.operation')" width="200">
          <div class="collect-table-operate" slot-scope="props">
            <!-- 回溯 -->
            <bk-button
              theme="primary"
              text
              class="mr10 king-button"
              v-cursor="{ active: !(props.row.permission && props.row.permission.manage_collection) }"
              @click.stop="operateHandler(props.row, 'restore')">
              {{ $t('logArchive.restore') }}
            </bk-button>
            <!-- 编辑 -->
            <bk-button
              theme="primary"
              text
              class="mr10 king-button"
              v-cursor="{ active: !(props.row.permission && props.row.permission.manage_collection) }"
              @click.stop="operateHandler(props.row, 'edit')">
              {{ $t('编辑') }}
            </bk-button>
            <!-- 删除 -->
            <bk-button
              theme="primary"
              text
              class="mr10 king-button"
              v-cursor="{ active: !(props.row.permission && props.row.permission.manage_collection) }"
              @click.stop="operateHandler(props.row, 'delete')">
              {{ $t('btn.delete') }}
            </bk-button>
          </div>
        </bk-table-column>
      </bk-table>
    </section>
    <!-- 新增/编辑归档 -->
    <ArchiveSlider
      v-if="isRenderSlider"
      :show-slider.sync="showSlider"
      :edit-archive="editArchive"
      @updated="handleUpdated"
    />

    <!-- 新增回溯 -->
    <RestoreSlider
      :show-slider.sync="showRestoreSlider"
      :archive-id="editArchiveId"
      @updated="handleUpdatedRestore"
    />
  </section>
</template>

<script>
import { mapGetters } from 'vuex';
import StateTable from './components/state-table.vue';
import ArchiveSlider from './components/archive-slider';
import RestoreSlider from '../archive-restore/restore-slider.vue';
import { formatFileSize } from '@/common/util';

export default {
  name: 'archive-list',
  components: {
    StateTable,
    ArchiveSlider,
    RestoreSlider,
  },
  data() {
    return {
      isTableLoading: false,
      isRenderSlider: true,
      showRestoreSlider: false,
      showSlider: false,
      keyword: '',
      curExpandArchiveId: '', // 展开当前归档项
      editArchiveId: null, // 回溯归档项id
      editArchive: null,
      dataList: [],
      pagination: {
        current: 1,
        count: 0,
        limit: 10,
        limitList: [10, 20, 50, 100],
      },
    };
  },
  computed: {
    ...mapGetters({
      bkBizId: 'bkBizId',
    }),
    repositoryFilters() {
      return [];
    },
  },
  created() {
    this.search();
  },
  methods: {
    search() {
      this.pagination.current = 1;
      this.requestData();
    },
    handleFilterChange() {},
    handleCreate() {
      this.editArchive = null;
      this.showSlider = true;
    },
    /**
     * 分页变换
     * @param  {Number} page 当前页码
     * @return {[type]}      [description]
     */
    handlePageChange(page) {
      if (this.pagination.current !== page) {
        this.pagination.current = page;
        this.requestData();
      }
    },
    /**
     * 分页限制
     * @param  {Number} page 当前页码
     * @return {[type]}      [description]
     */
    handleLimitChange(page) {
      if (this.pagination.limit !== page) {
        this.pagination.current = 1;
        this.pagination.limit = page;
        this.requestData();
      }
    },
    requestData() {
      this.isTableLoading = true;
      this.$http.request('archive/getArchiveList', {
        query: {
          ...this.params,
          keyword: this.keyword,
          bk_biz_id: this.bkBizId,
          page: this.pagination.current,
          pagesize: this.pagination.limit,
        },
      }).then((res) => {
        const { data } = res;
        this.pagination.count = data.total;
        this.dataList = data.list;
      })
        .catch((err) => {
          console.warn(err);
        })
        .finally(() => {
          this.isTableLoading = false;
        });
    },
    handleUpdated() {
      this.showSlider = false;
      this.search();
    },
    handleUpdatedRestore() {
      this.showRestoreSlider = false;
      this.editArchiveId = null;
    },
    operateHandler(row, operateType) {
      if (!(row.permission?.manage_collection)) {
        return this.getOptionApplyData({
          action_ids: ['manage_collection'],
          resources: [{
            type: 'collection',
            id: row.collector_config_id,
          }],
        });
      }

      if (operateType === 'restore') {
        this.editArchiveId = row.archive_config_id;
        this.showRestoreSlider = true;
      }

      if (operateType === 'edit') {
        this.editArchive = row;
        this.showSlider = true;
        return;
      }

      if (operateType === 'delete') {
        this.$bkInfo({
          type: 'warning',
          title: this.$t('logArchive.Confirm_delete_archive'),
          confirmFn: () => {
            this.requestDelete(row);
          },
        });
      }
    },
    requestDelete(row) {
      this.$http.request('archive/deleteArchive', {
        params: {
          archive_config_id: row.archive_config_id,
        },
      }).then((res) => {
        if (res.result) {
          const page = this.dataList.length <= 1
            ? (this.pagination.current > 1 ? this.pagination.current - 1 : 1)
            : this.pagination.current;
          this.messageSuccess(this.$t('删除成功'));
          if (page !== this.pagination.current) {
            this.handlePageChange(page);
          } else {
            this.requestData();
          }
        }
      })
        .catch(() => {});
    },
    async getOptionApplyData(paramData) {
      try {
        this.isTableLoading = true;
        const res = await this.$store.dispatch('getApplyData', paramData);
        this.$store.commit('updateAuthDialogData', res.data);
      } catch (err) {
        console.warn(err);
      } finally {
        this.isTableLoading = false;
      }
    },
    getFileSize(size) {
      return formatFileSize(size);
    },
  },
};
</script>

<style lang="scss">
  @import '@/scss/mixins/clearfix';
  @import '@/scss/conf';
  @import '@/scss/devops-common.scss';

  .log-archive-list {
    padding: 20px 24px;
    .top-operation {
      margin-bottom: 20px;
      @include clearfix;
      .bk-button {
        width: 120px;
      }
    }
    .list-search {
      width: 320px;
    }
    .archive-table {
      .filter-column {
        .cell {
          display: flex;
        }
      }
    }
    .bk-table-body td.bk-table-expanded-cell {
      padding: 0;
    }
  }
</style>
