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
  <div class="access-manage-container" v-bkloading="{ isLoading: basicLoading }">
    <auth-page v-if="authPageInfo" :info="authPageInfo"></auth-page>
    <template v-if="!authPageInfo && !basicLoading && collectorData">
      <bk-tab :active.sync="activePanel" type="border-card">
        <bk-tab-panel v-for="panel in panels" v-bind="panel" :key="panel.name"></bk-tab-panel>
      </bk-tab>
      <keep-alive>
        <component
          class="tab-content"
          :collector-data="collectorData"
          :index-set-id="collectorData.index_set_id"
          :is="dynamicComponent"
          @update-active-panel="activePanel = $event"></component>
      </keep-alive>
    </template>
  </div>
</template>

<script>
import AuthPage from '@/components/common/auth-page';
import BasicInfo from './BasicInfo';
import CollectionStatus from './CollectionStatus';
import DataStorage from './DataStorage';
import DataStatus from './data-status';
import UsageDetails from '@/views/manage/manage-access/components/usage-details';

export default {
  name: 'collection-item',
  components: {
    AuthPage,
    BasicInfo,
    CollectionStatus,
    DataStorage,
    DataStatus,
    UsageDetails,
  },
  data() {
    return {
      basicLoading: true,
      authPageInfo: null,
      collectorData: null,
      activePanel: this.$route.query.type || 'basicInfo',
      panels: [
        { name: 'basicInfo', label: this.$t('基本信息') },
        { name: 'collectionStatus', label: this.$t('采集状态') },
        { name: 'dataStorage', label: this.$t('数据存储') },
        { name: 'dataStatus', label: this.$t('数据状态') },
        { name: 'usageDetails', label: this.$t('使用详情') },
      ],
    };
  },
  computed: {
    dynamicComponent() {
      const componentMaP = {
        basicInfo: 'BasicInfo',
        collectionStatus: 'CollectionStatus',
        dataStorage: 'DataStorage',
        dataStatus: 'DataStatus',
        usageDetails: 'UsageDetails',
      };
      return componentMaP[this.activePanel] || 'BasicInfo';
    },
  },
  created() {
    this.initPage();
  },
  methods: {
    async initPage() {
      // 进入路由需要先判断权限
      try {
        const paramData = {
          action_ids: ['manage_collection'],
          resources: [{
            type: 'collection',
            id: this.$route.params.collectorId,
          }],
        };
        const res = await this.$store.dispatch('checkAndGetData', paramData);
        if (res.isAllowed === false) {
          this.authPageInfo = res.data;
          // 显示无权限页面
        } else {
          // 正常显示页面
          const { data: collectorData } = await this.$http.request('collect/details', {
            params: {
              collector_config_id: this.$route.params.collectorId,
            },
          });
          this.collectorData = collectorData;
          this.$store.commit('collect/setCurCollect', collectorData);
        }
      } catch (err) {
        console.warn(err);
      } finally {
        this.basicLoading = false;
      }
    },
  },
};
</script>
