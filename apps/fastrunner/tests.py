#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import datetime
import os
import time

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FasterRunner.settings')
django.setup()

from fastrunner.tasks import del_database_backup


del_database_backup()