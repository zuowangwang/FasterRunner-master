#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import datetime
from collections import Counter

from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from fastrunner import models, serializers
from fastrunner.utils.common import get_between_date, gen_summary


class ChartShow(GenericViewSet):
    """
    chart shows
    """
    serializer_class = serializers.APISerializer
    permission_classes = (DjangoModelPermissions,)

    def get_queryset(self):
        project_id = self.request.data.get('project')
        return models.Report.objects.filter(project_id=project_id)

    def get(self, request, **kwargs):
        """Get custom time api run data.

        """
        start_date = request.data.get('start_date')
        complete_date = request.data.get('complete_date')
        between_date = get_between_date(start_date, complete_date)

        result = {}
        for date in between_date:
            end = date + datetime.timedelta(days=1)
            charts_queryset = self.get_queryset().filter(update_time__gte=date, update_time__lte=end)
            debug_reports = charts_queryset.filter(type=1)
            asyn_reports = charts_queryset.filter(type=2)
            clock_reports = charts_queryset.filter(type=3)
            tmp = {
                'debug_task': gen_summary(debug_reports),
                'asyn_task': gen_summary(asyn_reports),
                'clock_task': gen_summary(clock_reports),
            }
            current_total = dict(sum(map(Counter, tmp.values()), Counter()))
            tmp['current_total'] = current_total
            result[date.strftime("%Y%m%d")] = tmp
        return Response(result)
