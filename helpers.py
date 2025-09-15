from datetime import datetime
import re
from urllib.parse import parse_qs

from core.constants import NUM_ADJACENT
from doctors.method import get_adjacent_pages, paginate_queryset
from doctors.models import MedicalHistory, Patient


class QueryStringHelper:
    def __init__(self, query_string, pk_set=dict()):
        self.params = parse_qs(query_string)
        self.query_set = None
        self.doctor_pk = pk_set.get("doctor_pk")
        self.patient_pk = pk_set.get("patient_pk")
        self.history_pk = pk_set.get("history_pk")
        self.num_page = None
        self.page_index = None
        self.adjacent_pages = None
        '''
        {
            'search': ['fmdklasfml'],
            'page': ['1'],
        }
        '''

    def get(self, key, default=""):
        # Get the value for the given key, return default if key is not present
        values = self.params.get(key)
        if values:
            # parse_qs returns a list of values for each key
            return values[0] if len(values) == 1 else ""
        return default

    def get_int(self, key, default=1):
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def is_date(self, string):
        date_formats = ["%Y-%m", "%Y-%m-%d"]
        for date_format in date_formats:
            try:
                datetime.strptime(string, date_format)
                return True
            except ValueError:
                continue
        return False

    def is_name(self, string):
        return True

    def filter_queryset_searched_month(self, date_string):
        date_formats = ["%Y-%m", "%Y-%m-%d"]

        for date_format in date_formats:
            try:
                date_obj = datetime.strptime(date_string, date_format)
                break
            except ValueError:
                continue

        year = date_obj.year
        month = date_obj.month

        return year, month

    def set_queryset(self, query_set):
        self.query_set = query_set

    def search_controller(self, query_set):
        self.set_queryset(query_set)
        search = self.get('search')
        if len(self.query_set) == 0:
            return self.query_set

        if len(search) > 0:
            if self.is_date(search) and self.patient_pk:
                year, month = self.filter_queryset_searched_month(search)
                self.query_set = self.query_set.filter(created__year=year, created__month=month,
                                                       patient_id=self.patient_pk)
            elif self.is_name(search) and self.doctor_pk:
                self.query_set = self.query_set.filter(patient_info__name=search, doctor_id=self.doctor_pk)
        else:
            pass
        return self.query_set

    def page_controller(self, query_set):
        self.set_queryset(query_set)
        if len(self.query_set) == 0:
            return self.query_set
        request_page: int = self.get_int("page")
        self.query_set, self.num_page, self.page_index = paginate_queryset(self.query_set, request_page)
        self.adjacent_pages: list = get_adjacent_pages(request_page, self.num_page, NUM_ADJACENT)
        return self.query_set
