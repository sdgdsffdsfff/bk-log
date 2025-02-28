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
  <div class="archive-slider-container">
    <bk-sideslider
      transfer
      :title="isEdit ? $t('logArchive.editArchive') : $t('logArchive.createArchive')"
      :is-show="showSlider"
      :width="676"
      :quick-close="false"
      @animation-end="$emit('hidden')"
      @update:isShow="updateIsShow">
      <div v-bkloading="{ isLoading: sliderLoading }" slot="content" class="archive-slider-content">
        <bk-form
          v-if="!sliderLoading"
          data-test-id="addNewArchive_div_formContainer"
          :model="formData"
          :label-width="150"
          :rules="basicRules"
          form-type="vertical"
          ref="validateForm"
          class="king-form">
          <bk-form-item
            :label="$t('logArchive.collectFormLabel')"
            required
            property="collector_config_id">
            <bk-select
              searchable
              v-model="formData.collector_config_id"
              data-test-id="formContainer_select_selectCollector"
              :clearable="false"
              :disabled="isEdit"
              @change="handleCollectorChange">
              <bk-option
                v-for="option in collectorList"
                :key="option.collector_config_id"
                :id="option.collector_config_id"
                :name="option.collector_config_name"
                :disabled="!option.permission.manage_collection">
                <!-- <div
                  v-if="!(option.permission && option.permission.manage_collection)"
                  class="option-slot-container no-authority"
                  @click.stop>
                  <span class="text">
                    <span>{{ option.collector_config_name }}</span>
                    <span style="color:#979ba5;">（{{ `#${option.collector_config_id}` }}）</span>
                  </span>
                  <span class="apply-text" @click.stop="applyProjectAccess(option)">{{ $t('申请权限') }}</span>
                </div>
                <div v-else v-bk-overflow-tips class="option-slot-container">
                  <span>{{ option.collector_config_name }}</span>
                  <span style="color:#979ba5;">（{{ `#${option.collector_config_id}` }}）</span>
                </div> -->
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item
            :label="$t('logArchive.archiveRepository')"
            required
            property="target_snapshot_repository_name">
            <bk-select
              v-model="formData.target_snapshot_repository_name"
              data-test-id="formContainer_select_selectStorehouse"
              :disabled="isEdit || !formData.collector_config_id">
              <bk-option
                v-for="option in repositoryRenderList"
                :key="option.repository_name"
                :id="option.repository_name"
                :name="option.repository_name"
                :disabled="!option.permission.manage_es_source">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item
            :label="$t('过期时间')"
            required
            property="snapshot_days">
            <bk-select
              style="width: 300px;"
              v-model="formData.snapshot_days"
              data-test-id="formContainer_select_selectExpireDate"
              :clearable="false">
              <div slot="trigger" class="bk-select-name">
                {{ formData.snapshot_days ? formData.snapshot_days + $t('天') : '' }}
              </div>
              <template v-for="(option, index) in retentionDaysList">
                <bk-option :key="index" :id="option.id" :name="option.name"></bk-option>
              </template>
              <div slot="extension" style="padding: 8px 0;">
                <bk-input
                  v-model="customRetentionDay"
                  size="small"
                  type="number"
                  :placeholder="$t('输入自定义天数')"
                  :show-controls="false"
                  @enter="enterCustomDay($event)"
                ></bk-input>
              </div>
            </bk-select>
          </bk-form-item>
          <bk-form-item style="margin-top:40px;">
            <bk-button
              theme="primary"
              class="king-button mr10"
              data-test-id="formContainer_button_handleSubmit"
              :loading="confirmLoading"
              @click.stop.prevent="handleConfirm">
              {{ $t('提交') }}
            </bk-button>
            <bk-button
              data-test-id="formContainer_button_handleCancel"
              @click="handleCancel">{{ $t('取消') }}</bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';

export default {
  props: {
    showSlider: {
      type: Boolean,
      default: false,
    },
    editArchive: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      confirmLoading: false,
      sliderLoading: false,
      customRetentionDay: '', // 自定义过期天数
      collectorList: [], // 采集项列表
      repositoryOriginList: [], // 仓库列表
      // repositoryRenderList: [], // 根据采集项关联的仓库列表
      retentionDaysList: [], // 过期天数列表
      formData: {
        snapshot_days: '',
        collector_config_id: '',
        target_snapshot_repository_name: '',
      },
      basicRules: {},
      requiredRules: {
        required: true,
        trigger: 'blur',
      },
    };
  },
  computed: {
    ...mapGetters({
      bkBizId: 'bkBizId',
      globalsData: 'globals/globalsData',
    }),
    isEdit() {
      return this.editArchive !== null;
    },
    repositoryRenderList() {
      let list = [];
      const collectorId = this.formData.collector_config_id;
      if (collectorId && this.collectorList.length && this.repositoryOriginList.length) {
        const curCollector = this.collectorList.find(collect => collect.collector_config_id === collectorId);
        const clusterId = curCollector.storage_cluster_id;
        list = this.repositoryOriginList.filter(item => item.cluster_id === clusterId);
      }

      return list;
    },
  },
  watch: {
    async showSlider(val) {
      if (val) {
        this.sliderLoading = this.isEdit;
        await this.getCollectorList();
        await this.getRepoList();
        this.updateDaysList();

        if (this.isEdit) {
          const {
            collector_config_id,
            target_snapshot_repository_name,
            snapshot_days,
          } = this.editArchive;
          Object.assign(this.formData, {
            collector_config_id,
            target_snapshot_repository_name,
            snapshot_days,
          });
        }
      } else {
        // 清空表单数据
        this.formData = {
          snapshot_days: '',
          collector_config_id: '',
          target_snapshot_repository_name: '',
        };
      }
    },
  },
  created() {
    this.basicRules = {
      collector_config_id: [this.requiredRules],
      target_snapshot_repository_name: [this.requiredRules],
      snapshot_days: [this.requiredRules],
    };
  },
  methods: {
    // 获取采集项列表
    getCollectorList() {
      const query = {
        bk_biz_id: this.bkBizId,
        have_data_id: 1,
      };
      this.$http.request('collect/getAllCollectors', { query }).then((res) => {
        const data = res.data;
        if (data.length) {
          this.collectorList = data;
        }
      });
    },
    // 获取归档仓库列表
    getRepoList() {
      this.$http.request('archive/getRepositoryList', {
        query: {
          bk_biz_id: this.bkBizId,
        },
      }).then((res) => {
        const { data } = res;
        this.repositoryOriginList = data || [];
      })
        .finally(() => {
          this.sliderLoading = false;
        });
    },
    handleCollectorChange() {
      this.formData.target_snapshot_repository_name = '';
    },
    updateIsShow(val) {
      this.$emit('update:showSlider', val);
    },
    handleCancel() {
      this.$emit('update:showSlider', false);
    },
    updateDaysList() {
      const retentionDaysList = [...this.globalsData.storage_duration_time].filter((item) => {
        return item.id;
      });
      this.retentionDaysList = retentionDaysList;
    },
    // 输入自定义过期天数
    enterCustomDay(val) {
      const numberVal = parseInt(val.trim(), 10);
      const stringVal = numberVal.toString();
      if (numberVal) {
        if (!this.retentionDaysList.some(item => item.id === stringVal)) {
          this.retentionDaysList.push({
            id: stringVal,
            name: stringVal + this.$t('天'),
          });
        }
        this.formData.snapshot_days = stringVal;
        this.customRetentionDay = '';
        document.body.click();
      } else {
        this.customRetentionDay = '';
        this.messageError(this.$t('请输入有效数值'));
      }
    },
    // 采集项列表点击申请采集项目管理权限
    async applyProjectAccess(item) {
      this.$el.click(); // 手动关闭下拉
      try {
        this.$bkLoading();
        const res = await this.$store.dispatch('getApplyData', {
          action_ids: ['manage_collection'],
          resources: [{
            type: 'collection',
            id: item.collector_config_id,
          }],
        });
        window.open(res.data.apply_url);
      } catch (err) {
        console.warn(err);
      } finally {
        this.$bkLoading.hide();
      }
    },
    async handleConfirm() {
      try {
        await this.$refs.validateForm.validate();
        let url = '/archive/createArchive';
        const params = {};
        let paramsData = {
          ...this.formData,
          bk_biz_id: this.bkBizId,
        };

        if (this.isEdit) {
          url = '/archive/editArchive';
          const { snapshot_days } = this.formData;
          const { archive_config_id } = this.editArchive;
          paramsData = {
            snapshot_days,
          };
          // eslint-disable-next-line camelcase
          params.archive_config_id = archive_config_id;
        }

        this.confirmLoading = true;
        await this.$http.request(url, {
          data: paramsData,
          params,
        });
        this.$bkMessage({
          theme: 'success',
          message: this.$t('保存成功'),
          delay: 1500,
        });
        this.$emit('updated');
      } catch (e) {
        console.warn(e);
      } finally {
        this.confirmLoading = false;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
  .archive-slider-content {
    height: calc(100vh - 60px);
    min-height: 394px;
    .king-form {
      padding: 10px 0 36px 36px;
      .bk-form-item {
        margin-top: 18px;
      }
      .bk-select {
        width: 300px;
      }
    }
  }
</style>
