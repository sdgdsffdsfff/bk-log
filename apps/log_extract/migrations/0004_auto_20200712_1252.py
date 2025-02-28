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
# Generated by Django 1.11.23 on 2020-07-12 04:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("log_extract", "0003_auto_20200701_1424"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="strategies",
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AlterModelOptions(
            name="tasks",
            options={"ordering": ["-updated_at"]},
        ),
        migrations.AddField(
            model_name="strategies",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="删除时间"),
        ),
        migrations.AddField(
            model_name="strategies",
            name="deleted_by",
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name="删除者"),
        ),
        migrations.AddField(
            model_name="strategies",
            name="is_deleted",
            field=models.BooleanField(default=False, verbose_name="是否删除"),
        ),
    ]
