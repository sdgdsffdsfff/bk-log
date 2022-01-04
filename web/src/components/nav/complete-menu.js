/*
 * Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 * BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
 *
 * License for BK-LOG 蓝鲸日志平台:
 * --------------------------------------------------------------------
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
 * and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all copies or substantial
 * portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
 * LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
 * NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

import i18n from '@/language/i18n';

export const menuArr = [
  {
    name: i18n.t('nav.retrieve'),
    id: 'retrieve',
    level: 1,
  },
  {
    name: i18n.t('nav.dashboard'),
    id: 'dashboard',
    level: 1,
    dropDown: true,
    children: [{
      id: 'create_dashboard',
      name: i18n.t('新建仪表盘'),
      level: 2,
      isDashboard: true,
      project_manage: true,
    }, {
      id: 'create_folder',
      name: i18n.t('新建目录'),
      level: 2,
      isDashboard: true,
      project_manage: true,
    }, {
      id: 'import_dashboard',
      name: i18n.t('导入仪表盘'),
      level: 2,
      isDashboard: true,
      project_manage: true,
    }],
  },
  {
    name: i18n.t('nav.extract'),
    id: 'extract',
    level: 1,
  },
  {
    name: i18n.t('trace.trace'),
    id: 'trace',
    level: 1,
  },
  {
    name: i18n.t('nav.monitors'),
    id: 'monitor',
    level: 1,
    children: [
      {
        name: i18n.t('nav.alarmStrategy'),
        id: 'alarmStrategy',
        level: 2,
        children: [
          {
            name: i18n.t('nav.addstrategy'),
            id: 'addstrategy',
            level: 3,
          },
          {
            name: i18n.t('nav.editstrategy'),
            id: 'editstrategy',
            level: 3,
          },
        ],
      },
    ],
  },
  {
    name: i18n.t('nav.manage'),
    id: 'manage',
    level: 1,
    dropDown: true,
    children: [
      {
        name: i18n.t('nav.dataSource'),
        id: 'manage',
        level: 2,
        children: [
          {
            name: i18n.t('nav.collectAccess'),
            id: 'collectAccess',
            level: 3,
            children: [
              {
                name: i18n.t('nav.New_acquisition'),
                id: 'collectAdd',
                level: 4,
              },
              {
                name: i18n.t('nav.Edit_collection'),
                id: 'collectEdit',
                level: 4,
              },
              {
                name: i18n.t('nav.Enable_collections'),
                id: 'collectStart',
                level: 4,
              },
              {
                name: i18n.t('nav.Disable_collection'),
                id: 'collectStop',
                level: 4,
              },
              {
                name: i18n.t('nav.Field_extraction'),
                id: 'collectField',
                level: 4,
              },
              {
                name: i18n.t('nav.Configuration_details'),
                id: 'allocation',
                level: 4,
                children: [
                  {
                    name: i18n.t('nav.Data_sampling'),
                    id: 'jsonFormat',
                    level: 5,
                  },
                ],
              },
            ],
          },
          {
            name: i18n.t('nav.esAccess'),
            id: 'esAccess',
            level: 3,
          },
        ],
      },
      {
        name: i18n.t('nav.indexSet'),
        id: 'indexSet',
        level: 2,
        children: [
          {
            name: i18n.t('nav.addIndexSet'),
            id: 'addIndexSet',
            level: 3,
          },
          {
            name: i18n.t('nav.editIndexSet'),
            id: 'editIndexSet',
            level: 3,
          },
        ],
      },
      {
        name: i18n.t('链路配置'),
        id: 'linkConfiguration',
        level: 2,
      },
      {
        name: i18n.t('nav.permissionGroup'),
        id: 'permissionGroup',
        level: 2,
      },
      {
        name: i18n.t('nav.v3Migrate'),
        id: 'migrate',
        level: 2,
      },
      {
        name: i18n.t('nav.extractManage'),
        id: 'manageExtract',
        level: 2,
      },
    ],
  },
];
