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
  <div class="repository-slider-container" data-test-id="archive_div_addNewStorehouse">
    <bk-sideslider
      transfer
      :title="isEdit ? $t('logArchive.editRepository') : $t('logArchive.createRepository')"
      :is-show="showSlider"
      :width="676"
      :quick-close="false"
      @animation-end="$emit('hidden')"
      @update:isShow="updateIsShow">
      <div v-bkloading="{ isLoading: sliderLoading }" slot="content" class="repository-slider-content">
        <bk-form
          v-if="!sliderLoading"
          :model="formData"
          :label-width="150"
          :rules="basicRules"
          form-type="vertical"
          ref="validateForm"
          class="king-form">
          <h3 class="form-title">{{ $t('基础信息') }}</h3>
          <bk-form-item
            ext-cls="es-cluster-item"
            :label="$t('ES集群')"
            required
            :rules="basicRules.cluster_id"
            property="cluster_id">
            <bk-select
              v-model="formData.cluster_id"
              searchable
              data-test-id="addNewStorehouse_select_selectEsCluster"
              @change="handleChangeCluster">
              <bk-option
                v-for="option in esClusterList"
                :key="option.cluster_config.cluster_id"
                :id="option.cluster_config.cluster_id"
                :name="option.cluster_config.cluster_name">
                <div
                  v-if="!(option.permission && option.permission.manage_es_source)"
                  class="option-slot-container no-authority"
                  @click.stop>
                  <span class="text">
                    <span>{{ option.cluster_config.cluster_name }}</span>
                  </span>
                  <span class="apply-text" @click="applyProjectAccess(option)">{{ $t('申请权限') }}</span>
                </div>
                <div v-else v-bk-overflow-tips class="option-slot-container">
                  <span>{{ option.cluster_config.cluster_name }}</span>
                </div>
              </bk-option>
            </bk-select>
            <p class="es-source" v-if="esClusterSource">
              <span>{{ $t('来源') }}：</span>
              <span>{{ esClusterSource }}</span>
            </p>
          </bk-form-item>
          <h3 class="form-title">{{ $t('logArchive.repositoryConfig') }}</h3>
          <bk-form-item :label="$t('logArchive.repositoryType')" ext-cls="repository-item" required>
            <div
              :class="{ 'repository-card': true, 'is-active': formData.es_config.type === card.id }"
              v-for="card in repository"
              :key="card.name"
              :data-test-id="`addNewStorehouse_div_${card.id}`"
              @click="changeRepository(card)">
              <span class="repository-name">{{ card.name }}</span>
              <img :src="card.image" class="card-image">
            </div>
          </bk-form-item>
          <bk-alert type="info">
            <div slot="title" class="repository-alert">
              <div v-if="formData.es_config.type === 'hdfs'">
                <p>{{ $t('logArchive.repositoryAlert1') }}</p>
                <p>{{ $t('logArchive.repositoryAlert2') }}</p>
              </div>
              <div v-if="formData.es_config.type === 'fs'">
                <p>{{ $t('logArchive.repositoryAlert3') }}</p>
              </div>
              <div v-if="formData.es_config.type === 'cos'">
                <p>{{ $t('logArchive.repositoryAlert4') }}</p>
              </div>
            </div>
          </bk-alert>
          <bk-form-item
            :label="$t('logArchive.repositoryName')"
            required
            property="snapshot_repository_name">
            <bk-input
              v-model="formData.snapshot_repository_name"
              data-test-id="addNewStorehouse_input_repoName"
              :placeholder="$t('logArchive.repoNmaeTip')">
            </bk-input>
          </bk-form-item>
          <!-- HDFS -->
          <div v-if="formData.es_config.type === 'hdfs'" key="hdfs">
            <bk-form-item
              :label="$t('logArchive.archiveDirectory')"
              required
              :rules="basicRules.path"
              :property="formData.hdfsFormData.path">
              <bk-input
                v-model="formData.hdfsFormData.path"
                data-test-id="addNewStorehouse_input_archiveCatalog"></bk-input>
            </bk-form-item>
            <bk-form-item
              :label="$t('logArchive.HDFSAddr')"
              required
              :rules="basicRules.uri"
              :property="formData.hdfsFormData.uri">
              <bk-input
                v-model="formData.hdfsFormData.uri"
                data-test-id="addNewStorehouse_input_HDFSurl">
                <!-- <template slot="prepend">
                  <div class="group-text">hdfs://</div>
                </template> -->
              </bk-input>
            </bk-form-item>
            <bk-form-item
              label="Principal"
              required
              :rules="basicRules.principal"
              :property="formData.hdfsFormData.security.principal">
              <div class="principal-item">
                <bk-switcher
                  size="large"
                  theme="primary"
                  v-model="formData.hdfsFormData.isSecurity">
                </bk-switcher>
                <bk-input
                  v-model="formData.hdfsFormData.security.principal"
                  data-test-id="addNewStorehouse_input_principal"></bk-input>
              </div>
            </bk-form-item>
          </div>
          <!-- FS -->
          <div v-if="formData.es_config.type === 'fs'" key="fs">
            <bk-form-item
              :label="$t('logArchive.archiveDirectory')"
              data-test-id="addNewStorehouse_input_archiveCatalog"
              required
              :rules="basicRules.location"
              :property="formData.fsFormData.location">
              <bk-input v-model="formData.fsFormData.location"></bk-input>
            </bk-form-item>
          </div>
          <!-- COS -->
          <div v-if="formData.es_config.type === 'cos'" key="cos">
            <bk-form-item
              :label="$t('logArchive.archiveDirectory')"
              required
              :rules="basicRules.base_path"
              :property="formData.cosFormData.base_path">
              <bk-input
                v-model="formData.cosFormData.base_path"
                data-test-id="addNewStorehouse_input_archiveCatalog"></bk-input>
            </bk-form-item>
            <bk-form-item
              :label="$t('logArchive.region')"
              required
              :rules="basicRules.region"
              :property="formData.cosFormData.region">
              <bk-input
                v-model="formData.cosFormData.region"
                data-test-id="addNewStorehouse_input_region"></bk-input>
            </bk-form-item>
            <bk-form-item
              label="Secretld"
              required
              :rules="basicRules.access_key_id"
              :property="formData.cosFormData.access_key_id">
              <bk-input
                v-model="formData.cosFormData.access_key_id"
                data-test-id="addNewStorehouse_input_Secretld"></bk-input>
            </bk-form-item>
            <bk-form-item
              label="SecretKey"
              required
              :rules="basicRules.access_key_secret"
              :property="formData.cosFormData.access_key_secret">
              <bk-input
                v-model="formData.cosFormData.access_key_secret"
                data-test-id="addNewStorehouse_input_SecretKey"></bk-input>
            </bk-form-item>
            <bk-form-item
              label="APPID"
              required
              :rules="basicRules.app_id"
              :property="formData.cosFormData.app_id">
              <bk-input
                v-model="formData.cosFormData.app_id"
                data-test-id="addNewStorehouse_input_APPID"></bk-input>
            </bk-form-item>
            <bk-form-item
              :label="$t('logArchive.BucketName')"
              required
              :rules="basicRules.bucket"
              :property="formData.cosFormData.bucket">
              <bk-input
                v-model="formData.cosFormData.bucket"
                data-test-id="addNewStorehouse_input_BucketName"></bk-input>
            </bk-form-item>
          </div>
          <bk-form-item style="margin-top:40px;">
            <bk-button
              theme="primary"
              class="king-button mr10"
              data-test-id="addNewStorehouse_button_submit"
              :loading="confirmLoading"
              @click.stop.prevent="handleConfirm">
              {{ $t('提交') }}
            </bk-button>
            <bk-button
              data-test-id="addNewStorehouse_button_cancel"
              @click="handleCancel">{{ $t('取消') }}</bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';

const cosConfigForm = () => {
  return {
    app_id: '',
    access_key_id: '',
    access_key_secret: '',
    bucket: '',
    region: '',
    compress: true,
  };
};

const hdfsConfigForm = () => {
  return {
    uri: '',
    path: '',
    isSecurity: false,
    compress: true,
    security: {
      principal: '',
    },
  };
};

const fsConfigForm = () => {
  return {
    location: '',
  };
};

export default {
  props: {
    showSlider: {
      type: Boolean,
      default: false,
    },
    editClusterId: {
      type: Number,
      default: null,
    },
  },
  data() {
    return {
      confirmLoading: false,
      sliderLoading: false,
      esClusterSource: '',
      esClusterList: [],
      repository: [
        { id: 'hdfs', name: 'HDFS', image: require('@/images/hdfs.png') },
        { id: 'fs', name: this.$t('logArchive.sharedDirectory'), image: require('@/images/fs.png') },
        { id: 'cos', name: 'COS', image: require('@/images/cos.png') },
      ],
      formData: {
        cluster_id: '',
        snapshot_repository_name: '',
        es_config: {
          type: 'hdfs',
        },
        cosFormData: cosConfigForm(),
        hdfsFormData: hdfsConfigForm(),
        fsFormData: fsConfigForm(),
      },
      requiredRules: {
        required: true,
        trigger: 'blur',
      },
      basicRules: {},
    };
  },
  computed: {
    ...mapGetters({
      bkBizId: 'bkBizId',
    }),
    isEdit() {
      return this.editClusterId !== null;
    },
  },
  watch: {
    showSlider(val) {
      if (val) {
        this.getEsClusterList();
        if (this.isEdit) {
        } else {
          //
        }
      } else {
        // 清空表单数据
        this.formData = {
          cluster_id: '',
          snapshot_repository_name: '',
          es_config: {
            type: 'hdfs',
          },
          cosFormData: cosConfigForm(),
          hdfsFormData: hdfsConfigForm(),
          fsFormData: fsConfigForm(),
        };
      }
    },
  },
  created() {
    this.basicRules = {
      cluster_id: [this.requiredRules],
      snapshot_repository_name: [
        {
          regex: /^[A-Za-z0-9_]+$/,
          trigger: 'blur',
        },
      ],
      path: [this.requiredRules],
      uri: [this.requiredRules],
      principal: [
        {
          validator: () => {
            const { isSecurity, security } = this.formData.hdfsFormData;
            if (isSecurity && security.principal.trim() === '') {
              return false;
            }
            return true;
          },
          trigger: 'blur',
        },
      ],
      location: [this.requiredRules],
      base_path: [this.requiredRules],
      region: [this.requiredRules],
      access_key_id: [this.requiredRules],
      access_key_secret: [this.requiredRules],
      app_id: [this.requiredRules],
      bucket: [this.requiredRules],
    };
  },
  methods: {
    async getEsClusterList() {
      const res = await this.$http.request('/source/list', {
        query: {
          bk_biz_id: this.bkBizId,
        },
      });
      if (res.data) {
        this.esClusterList = res.data;
        // this.esClusterList = res.data.filter(item => !item.cluster_config.is_default_cluster);
      }
    },
    handleChangeCluster(value) {
      const curCluster = this.esClusterList.find(cluster => cluster.cluster_config.cluster_id === value);
      this.esClusterSource = curCluster.source_name || '';
    },
    updateIsShow(val) {
      this.$emit('update:showSlider', val);
    },
    handleCancel() {
      this.$emit('update:showSlider', false);
    },
    changeRepository(card) {
      if (this.formData.es_config.type !== card.id) {
        this.$refs.validateForm.clearError();
        this.formData.es_config.type = card.id;
      }
    },
    async handleConfirm() {
      try {
        await this.$refs.validateForm.validate();
        const url = '/archive/createRepository';
        const {
          cluster_id,
          snapshot_repository_name,
          es_config,
          hdfsFormData,
          fsFormData,
          cosFormData,
        } = this.formData;
        const paramsData = {
          cluster_id,
          snapshot_repository_name,
          alias: snapshot_repository_name,
          es_config: {
            type: es_config.type,
          },
        };
        if (es_config.type === 'hdfs') {
          const { uri, path, isSecurity, security, compress  } = hdfsFormData;
          const principal = isSecurity ? security.principal : undefined;
          paramsData.es_config.settings = {
            uri,
            path,
            compress,
            'security.principal': principal,
          };
        }
        if (es_config.type === 'fs') {
          paramsData.es_config.settings = { ...fsFormData };
        }
        if (es_config.type === 'cos') {
          paramsData.es_config.settings = { ...cosFormData };
        }

        this.confirmLoading = true;
        await this.$http.request(url, {
          data: paramsData,
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
    // es集群管理权限申请
    async applyProjectAccess(option) {
      this.$el.click(); // 手动关闭下拉
      try {
        this.$bkLoading();
        const res = await this.$store.dispatch('getApplyData', {
          action_ids: ['manage_es_source'],
          resources: [{
            type: 'es_source',
            id: option.cluster_config.cluster_id,
          }],
        });
        window.open(res.data.apply_url);
      } catch (err) {
        console.warn(err);
      } finally {
        this.$bkLoading.hide();
      }
    },
  },
};
</script>

<style lang="scss">
  .repository-slider-content {
    min-height: 394px;
    .bk-form.bk-form-vertical {
      padding: 0 0 26px 36px;
      .bk-form-content {
        width: 500px;
      }
      .bk-form-item {
        margin-top: 12px;
        padding-left: 34px;
      }
      .bk-alert {
        width: 500px;
        margin: 10px 0 12px 34px;
      }
      .bk-select,
      .bk-date-picker {
        width: 300px;
      }
      .es-cluster-item {
        display: flex;
        margin-top: 16px;
        .bk-label {
          width: auto !important;
        }
        .bk-form-content {
          display: flex;
        }
        .bk-select {
          width: 240px;
        }
        .es-source {
          margin-left: 10px;
          font-size: 14px;
          color: #63656e;
        }
      }
      .repository-item {
        display: inline-block;
      }
      .repository-card {
        position: relative;
        float: left;
        width: 158px;
        height: 76px;
        margin-right: 12px;
        padding: 12px;
        background: #f5f7fa;
        border-radius: 2px;
        font-size: 14px;
        color: #63656e;
        border: 1px solid #f5f7fa;
        cursor: pointer;
        &:last-child {
          margin-right: 0;
        }
        &.is-active {
          color: #3a84ff;
          background: #e1ecff;
          border: 1px solid #a3c5fd;
        }
      }
      .card-image {
        position: absolute;
        right: 20px;
        bottom: 10px;
      }
    }
    .form-title {
      margin: 24px 40px 0 0;
      padding: 0 0 8px 10px;
      font-size: 14px;
      font-weight: 600;
      color: #63656e;
      line-height: 20px;
      border-bottom: 1px solid #dcdee5;
    }
    .repository-alert {
      padding-right: 10px;
    }
    .principal-item {
      display: flex;
      align-items: center;
      .bk-switcher {
        margin-right: 16px;
      }
      .bk-form-control {
        flex: 1;
      }
    }
  }
  .option-slot-container {
    padding: 8px 0;
    min-height: 32px;
    line-height: 14px;

    &.no-authority {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: #c4c6cc;
      cursor: not-allowed;

      .text {
        width: calc(100% - 56px);
      }

      .apply-text {
        flex-shrink: 0;
        display: none;
        color: #3a84ff;
        cursor: pointer;
      }

      &:hover .apply-text {
        display: flex;
      }
    }
  }
</style>
