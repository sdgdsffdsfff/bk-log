# Generated by Django 2.2.6 on 2021-10-19 02:44
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

from django.db import migrations, models
import django_jsonfield_backport.models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AiopsModel",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="是否删除")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="删除时间")),
                ("deleted_by", models.CharField(blank=True, max_length=32, null=True, verbose_name="删除者")),
                ("model_id", models.CharField(db_index=True, max_length=128, verbose_name="模型ID")),
                ("model_name", models.CharField(db_index=True, max_length=128, verbose_name="模型名称")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="AiopsModelExperiment",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="是否删除")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="删除时间")),
                ("deleted_by", models.CharField(blank=True, max_length=32, null=True, verbose_name="删除者")),
                ("model_id", models.CharField(db_index=True, max_length=128, verbose_name="模型ID")),
                ("experiment_id", models.IntegerField(db_index=True, verbose_name="实验id")),
                ("experiment_alias", models.CharField(db_index=True, max_length=128, verbose_name="实验名称")),
                ("status", models.CharField(blank=True, max_length=128, null=True, verbose_name="实验状态")),
                ("basic_model_id", models.CharField(blank=True, max_length=128, null=True, verbose_name="最新模型实例id")),
                (
                    "node_id_list",
                    django_jsonfield_backport.models.JSONField(blank=True, null=True, verbose_name="节点列表"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SampleSet",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="创建时间")),
                ("created_by", models.CharField(default="", max_length=32, verbose_name="创建者")),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True, null=True, verbose_name="更新时间")),
                ("updated_by", models.CharField(blank=True, default="", max_length=32, verbose_name="修改者")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="是否删除")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="删除时间")),
                ("deleted_by", models.CharField(blank=True, max_length=32, null=True, verbose_name="删除者")),
                ("sample_set_id", models.IntegerField(db_index=True, verbose_name="样本集ID")),
                ("sample_set_name", models.CharField(db_index=True, max_length=128, verbose_name="样本集名称")),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
