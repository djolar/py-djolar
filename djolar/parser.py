# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q
from django.http.request import QueryDict

import re


class DjangoSearchParser(object):
    '''
    Query string Format:
        q=key1__eq__value1|key2__lt__value2|key3__co__value3&s=order&extrafield=value
        Syntax:
        1. contains                 =>  key__co__value
                                    * sql equal: `key like '%value%'`
        2. exactly match            =>  key__eq__value,
                                        url encoded: key%3A%22value%22
                                    * sql equal: `key = 'value'`
        3. `in` operator            =>  key__in__[value1,value2,value3]
                                    * sql equal:`key in (value1,value2,value3)`
        4. `not` operator(AND)      =>  key__ni__[value1,value2]
                                    * sql equal: `key not in (value1,value2)`
        5. less than (lt)           =>  key__lt__value
                                    * sql equal: `key < value`
        6. less than or equal(lte) => key__lte__value
                                    * sql equal: `key <= value`
        7. great than (gt)          =>  key__gt__value
                                    * sql equal: `key > value`
        8. great than or equal(lte) => key__gte__value
                                    * sql equal: `key >= value`
    '''
    def __init__(self, *args, **kwargs):
        try:
            getattr(self, 'query_mapping')
        except AttributeError:
            raise AttributeError(
                'query_mapping is not defined in the subclass'
            )

        try:
            default = getattr(self, 'default_search')
            assert isinstance(default, dict), \
                'default_search should be instance of dict'
        except AttributeError:
            pass

        try:
            force = getattr(self, 'force_search')
            assert isinstance(force, dict), \
                'force_search should be instance of dict'
        except AttributeError:
            pass

        try:
            defaultOrderby = getattr(self, 'default_order_by')
            assert isinstance(defaultOrderby, list) or \
                isinstance(defaultOrderby, tuple), \
                'default_order_by should be instance of tuple/list'
        except AttributeError:
            pass

        try:
            self.ignoreCase = getattr(self, 'ignore_case')
            assert isinstance(self.ignoreCase, bool), \
                'ignore_case should be true/false'
        except AttributeError:
            self.ignoreCase = True

    def _build_q(self, key, field_fmt, value):
        '''
        Build a Q object
        :param  key, The key for the query_mapping to retrieve mapping field
        :param  field_fmt, The format to build the Q field name
        :param  value, The value for the Q field
        :return Q object
        '''
        tmpQueryObj = None
        try:
            mapField = self.query_mapping[key]
        except KeyError:
            return None
        if isinstance(mapField, (list, tuple)):
            for idx, field in enumerate(mapField):
                field_dict = {}
                field_dict[field_fmt.format(field)] = value
                if idx == 0:
                    tmpQueryObj = Q(**field_dict)
                else:
                    tmpQueryObj = tmpQueryObj | Q(**field_dict)
        elif isinstance(mapField, str):
            field_dict = {}
            field_dict[field_fmt.format(mapField)] = value
            tmpQueryObj = Q(**field_dict)
        else:
            raise ValueError(
                """the query_maping key value should be type of
                list/tuple or str"""
            )
        return tmpQueryObj

    def get_query_fields(self, requestParams):
        '''
        Get model query fields, eg.  Q(aa__contains='123') & Q(bb='123')
        :param   requestParams, The query dict get from request
        :return  Q query objects combines with `and` operator
        '''
        assert isinstance(requestParams, QueryDict), \
            'requestParams should be QueryDict'

        # Build force search
        try:
            forceSearch = getattr(self, 'force_search')
            queryObj = Q(**forceSearch)
        except AttributeError:
            queryObj = Q()

        # Build custom search
        if 'q' in requestParams.keys():
            keys = requestParams['q']
            for fields in keys.split('|'):
                if len(fields) == 0:
                    continue

                match = re.match(r'(\w+)__co__(\S+)', fields)
                if match:
                    # Contain
                    k, v = match.groups()
                    # Fuzzy match
                    if self.ignoreCase:
                        fieldQ = self._build_q(k, '{}__icontains', v)
                    else:
                        fieldQ = self._build_q(k, '{}__contains', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__lt__(\S+)', fields)
                if match:
                    # less than
                    k, v = match.groups()
                    fieldQ = self._build_q(k, '{}__lt', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__gt__(\S+)', fields)
                if match:
                    # greater than
                    k, v = match.groups()
                    fieldQ = self._build_q(k, '{}__gt', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__lte__(\S+)', fields)
                if match:
                    # less than and equal
                    k, v = match.groups()
                    fieldQ = self._build_q(k, '{}__lte', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__gte__(\S+)', fields)
                if match:
                    # greater than and equal
                    k, v = match.groups()
                    fieldQ = self._build_q(k, '{}__gte', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__eq__(\S+)', fields)
                if match:
                    # Exactly match
                    k, v = match.groups()
                    fieldQ = self._build_q(k, '{}', v)
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__in__\[(\S+)\]', fields)
                if match:
                    # `in` operator
                    k, v = match.groups()
                    fieldQ = self._build_q(
                        k,
                        '{}__in',
                        [i.strip() for i in v.split(',')]
                    )
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                match = re.match(r'(\w+)__ni__\[(\S+)\]', fields)
                if match:
                    # `not` operator
                    k, v = match.groups()
                    fieldQ = self._build_q(
                        k,
                        '{}__in',
                        [i.strip() for i in v.split(',')]
                    )
                    if not fieldQ:
                        continue
                    queryObj &= ~fieldQ
                    continue
        else:
            # Build default search if custom search provide no value
            try:
                defaultSearch = getattr(self, 'default_search')
                dftQueryObj = Q(**defaultSearch)
                queryObj &= dftQueryObj
            except AttributeError:
                pass

        return queryObj

    def get_order_fields(self, requestParams):
        '''
        Get order by field
        :param  requestParams, The query dict get from request
        :return Order by field name, if desc return [`-field`],
        if asc, return [`field`];
        if order by param not provided, then look for `default_order_by`
        if `default_order_by` is not provided, then return [`pk`] as default
        '''
        assert isinstance(requestParams, QueryDict), \
            'requestParams should be QueryDict'

        if 's' in requestParams.keys():
            value = requestParams['s']
            if value != '':
                fields = value.split(',')
                orderby = []
                for field in fields:
                    m = re.search('(?<=-)\S+', field)
                    if m:
                        # Desc
                        orderby.append('-{}'.format(self.query_mapping[m.group()]))
                    else:
                        # Asc
                        orderby.append(self.query_mapping[field])

                return orderby

        # Default to user setting
        try:
            defaultOrderby = getattr(self, 'default_order_by')
            if len(defaultOrderby) == 0:
                return ['pk']
            else:
                return defaultOrderby
        except AttributeError:
            return ['pk']


class BaseSearcher(DjangoSearchParser):
    def __init__(self, classtype):
        self._type = classtype


def ClassFactory(name, argnames, BaseClass=BaseSearcher):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            # here, the argnames variable is the one passed to the
            # ClassFactory call
            if key not in argnames:
                raise TypeError(
                    "Argument %s not valid for %s" % 
                    (key, self.__class__.__name__)
                )
            setattr(self, key, value)
        BaseSearcher.__init__(self, name[:-len("Class")])
    newclass = type(name, (BaseSearcher,), {"__init__": __init__})
    return newclass
