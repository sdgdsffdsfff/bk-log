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
  <div class="main-container create-task-container">
    <div class="row-container">
      <div class="title">
        {{ $t('下载目标') }}
        <span class="required">*</span>
      </div>
      <div class="content">
        <div class="flex-box">
          <bk-button
            theme="primary"
            @click="showSelectDialog = true"
            data-test-id="addNewExtraction_button_selectTheServer"
          >{{ $t('选择服务器') }}</bk-button>
          <div class="select-text">
            {{ $t('已选择') }}
            <span class="primary" v-if="ipList.length">{{ ipList.length }}</span>
            <span class="error" v-else>{{ ipList.length }}</span>
            {{ $t('个节点') }}
          </div>
        </div>
        <IpSelect :show-select-dialog.sync="showSelectDialog" @confirm="handleConfirm"></IpSelect>
      </div>
    </div>

    <div class="row-container">
      <div class="title">
        {{ $t('目录或文件名') }}
        <span class="required">*</span>
        <span class="log-icon icon-info-fill" v-bk-tooltips="$t('查询目录提示')"></span>
      </div>
      <div class="content">
        <FilesInput
          v-model="fileOrPath"
          :available-paths="availablePaths"
          @update:select="handleFilesSelect">
        </FilesInput>
      </div>
    </div>

    <div class="row-container">
      <div class="title">{{ $t('预览地址') }}</div>
      <PreviewFiles
        ref="preview"
        v-model="downloadFiles"
        :ip-list="ipList"
        :file-or-path="fileOrPath"
        @update:fileOrPath="handleFileOrPathUpdate">
      </PreviewFiles>
    </div>

    <div class="row-container">
      <div class="title">{{ $t('文本过滤') }}</div>
      <div class="content">
        <TextFilter ref="textFilter"></TextFilter>
      </div>
    </div>

    <div class="row-container">
      <div class="title">{{ $t('备注') }}</div>
      <div class="content">
        <bk-input v-model="remark" style="width: 261px;"></bk-input>
      </div>
    </div>
    <div class="row-container">
      <div class="title">{{ $t('提取链路') }}</div>
      <div class="content">
        <!-- eslint-disable-next-line vue/camelcase -->
        <bk-select v-model="link_id"
                   style="width: 250px;margin-right: 20px;background-color: #fff;"
                   data-test-id="addNewExtraction_select_selectLink"
                   :clearable="false">
          <bk-option
            v-for="link in extractLinks"
            :key="link.link_id"
            :id="link.link_id"
            :name="link.show_name">
          </bk-option>
        </bk-select>
      </div>
      <div class="content">{{$t("选择离你最近的提取链路")}}</div>
    </div>

    <div class="button-container">
      <bk-button
        theme="primary" style="margin-right: 16px;width: 120px;"
        data-test-id="addNewExtraction_button_submitConfigure"
        :disabled="canSubmit" @click="handleSubmit">
        {{ $t('提交下载任务') }}
      </bk-button>
      <bk-button
        style="width: 120px;" @click="goToHome"
        data-test-id="addNewExtraction_button_cancel"
      >{{ $t('取消') }}</bk-button>
    </div>
  </div>
</template>

<script>
import IpSelect from '@/views/extract/create/IpSelect';
import FilesInput from '@/views/extract/create/FilesInput';
import TextFilter from '@/views/extract/create/TextFilter';
import PreviewFiles from '@/views/extract/create/PreviewFiles';

export default {
  name: 'ExtractCreate',
  components: {
    IpSelect,
    FilesInput,
    TextFilter,
    PreviewFiles,
  },
  data() {
    return {
      showSelectDialog: false,
      ipList: [], // 下载目标
      fileOrPath: '', // 目录
      availablePaths: [], // 目录可选列表
      downloadFiles: [], // 下载的文件
      remark: '', // 备注
      extractLinks: [], // 提取链路
      link_id: null,
    };
  },
  computed: {
    canSubmit() {
      // eslint-disable-next-line eqeqeq
      return (!this.ipList.length || !this.downloadFiles.length) && this.link_id != null;
    },
  },
  mounted() {
    this.checkIsClone();
    this.getExtractLinkList();
  },
  methods: {
    async checkIsClone() {
      if (this.$route.name === 'extract-clone' && sessionStorage.getItem('cloneData')) {
        const cloneData = JSON.parse(sessionStorage.getItem('cloneData'));
        sessionStorage.removeItem('cloneData');

        this.ipList = cloneData.ip_list; // 克隆下载目标
        this.fileOrPath = cloneData.preview_directory; // 克隆目录
        this.$refs.textFilter.handleClone(cloneData); // 克隆文本过滤
        this.remark = cloneData.remark; // 克隆备注
        // 获取目录下拉列表和预览地址
        this.handleCloneAvailablePaths(cloneData);
        this.$nextTick(() => {
          this.$refs.preview.handleClone(cloneData);
        });
      }
    },
    getExtractLinkList() {
      this.$http.request('extract/getExtractLinkList', {
        data: { bk_biz_id: this.$store.state.bkBizId },
      })
        .then((res) => {
          this.extractLinks = res.data;
          this.link_id = this.extractLinks[0].link_id;
        })
        .catch((e) => {
          console.warn(e);
        });
    },
    handleCloneAvailablePaths(cloneData) {
      this.$http.request('extract/getAvailableExplorerPath', {
        data: {
          bk_biz_id: this.$store.state.bkBizId,
          ip_list: cloneData.ip_list,
        },
      }).then((res) => {
        this.availablePaths = res.data.map(item => item.file_path);
      })
        .catch((e) => {
          console.warn(e);
        });
    },
    handleFileOrPathUpdate(fileOrPath) {
      this.fileOrPath = fileOrPath;
    },
    handleFilesSelect(fileOrPath) {
      this.$refs.preview.getExplorerList({ path: fileOrPath });
    },
    handleConfirm(ipList, availablePaths) {
      this.ipList = ipList;
      this.availablePaths = availablePaths;
    },
    handleSubmit() {
      this.$emit('loading', true);
      // 根据预览地址选择的文件提交下载任务
      this.$http.request('extract/createDownloadTask', {
        data: {
          bk_biz_id: this.$store.state.bkBizId,
          ip_list: this.ipList, // 下载目标
          preview_directory: this.fileOrPath, // 目录
          preview_ip: this.$refs.preview.previewIp.join(','), // 预览地址
          preview_time_range: this.$refs.preview.timeRange, // 文件日期
          preview_start_time: this.$refs.preview.timeStringValue[0], // 文件日期
          preview_end_time: this.$refs.preview.timeStringValue[1], // 文件日期
          preview_is_search_child: this.$refs.preview.isSearchChild, // 是否搜索子目录
          file_path: this.downloadFiles, // 下载文件
          filter_type: this.$refs.textFilter.filterType, // 过滤类型
          filter_content: this.$refs.textFilter.filterContent, // 过滤内容
          remark: this.remark, // 备注
          link_id: this.link_id,
        },
      }).then(() => {
        this.goToHome();
      })
        .catch((err) => {
          console.warn(err);
          this.$emit('loading', false);
        });
    },
    goToHome() {
      this.$router.push({
        name: 'log-extract-task',
        query: {
          projectId: window.localStorage.getItem('project_id'),
        },
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.create-task-container {
  margin-top: 20px;
  padding: 20px 24px;
  background-color: #FFF;
  color: #63656e;
  border: 1px solid #dcdee5;
  .row-container {
    display: flex;
    min-height: 40px;
    margin: 20px 0 24px;
    .title {
      width: 128px;
      margin-right: 16px;
      font-size: 16px;
      line-height: 40px;
      font-size: 14px;
      text-align: right;
      .required {
        font-size: 16px;
        color: #ea3636;
      }
      .icon-info-fill {
        color: #979ba5;
        cursor: pointer;
      }
    }
    .content {
      display: flex;
      flex-flow: column;
      justify-content: center;
      min-height: 40px;
      .flex-box {
        display: flex;
        align-items: center;
        .select-text {
          margin-left: 12px;
          font-size: 12px;
          line-height: 16px;
          .primary {
            color: #3a84ff;
          }
          .error {
            color: #ea3636;
          }
        }
      }
    }
  }
  .button-container {
    margin: 32px 0 0 144px;
  }
}
</style>
