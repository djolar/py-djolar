# encoding: utf-8
from django.db.models import Q
import re


class DjangoSearchParser(object):
    '''
    Query string Format:
        q=key1:value1+key2:value2+key3:value3&s=order&extrafield=value

        Syntax:
        1. contains                 =>  key:value
                                    * sql equal: `key like '%value%'`
        2. exactly match            =>  key:"value", url encoded: key%3A%22value%22
                                    * sql equal: `key = 'value'`
        3. `in` operator            =>  key:[value1,value2,value3], url encoded: key%3A%5Bvalue1%2Cvalue2%2Cvalue3%5D
                                    * sql equal: `key in (value1, value2, value3)`
        4. `not` operator(AND)      =>  key:~[value1,value2,value3], url encoded: key%3A%7E%5Bvalue1%2Cvalue2%2Cvalue3%5D
                                    * sql equal: `key not in (value1, value2, value3)`
        5. less than (lt)           =>  key<value
                                    * sql equal: `key < value`
        6. less than or equal(lte) => key|<value
                                    * sql equal: `key <= value`
        7. great than (gt)          =>  key>value
                                    * sql equal: `key > value`
        8. great than or equal(lte) => key|>value
                                    * sql equal: `key >= value`

    '''
    def __init__(self, *args, **kwargs):
        try:
            getattr(self, 'query_mapping')
        except AttributeError:
            raise AttributeError('query_mapping is not defined in the subclass')

        try:
            default = getattr(self, 'default_search')
            assert isinstance(default, dict), 'default_search should be instance of dict'
        except AttributeError:
            pass

        try:
            force = getattr(self, 'force_search')
            assert isinstance(force, dict), 'force_search should be instance of dict'
        except AttributeError:
            pass

        try:
            defaultOrderby = getattr(self, 'default_order_by')
            assert isinstance(defaultOrderby, list) or isinstance(defaultOrderby, tuple), \
                'default_order_by should be instance of tuple/list'
        except AttributeError:
            pass

        try:
            self.ignoreCase = getattr(self, 'ignore_case')
            assert isinstance(self.ignoreCase, bool), 'ignore_case should be true/false'
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
                tmpQueryObj = Q(**field_dict) if idx == 0 else tmpQueryObj | Q(**field_dict)
        elif isinstance(mapField, str):
            field_dict = {}
            field_dict[field_fmt.format(mapField)] = value
            tmpQueryObj = Q(**field_dict)
        else:
            raise ValueError('the query_maping key value should be type of list/tuple or str/unicode')
        return tmpQueryObj

    def get_query_fields(self, requestParams):
        '''
        Get model query fields, eg.  Q(aa__contains='123') & Q(bb='123')

        :param   requestParams, The query dict get from request
        :return  Q query objects combines with `and` operator
        '''
        assert isinstance(requestParams, QueryDict), 'requestParams should be QueryDict'

        # Build force search
        try:
            forceSearch = getattr(self, 'force_search')
            queryObj = Q(**forceSearch)
        except AttributeError:
            queryObj = Q()

        # Build custom search
        if 'q' in requestParams.keys():
            keys = requestParams['q']
            for fields in keys.split('+'):
                if len(fields) == 0:
                    continue

                # field_dict = {}
                k, v = fields.split(':')

                # If no value is provided, then ignore this keyword
                if v == '':
                    continue

                exactValue = re.match(r'^\<(.*)$', v)
                if exactValue:
                    # less than
                    fieldQ = self._build_q(k, '{}__lt', exactValue.groups()[0])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\|\<(.*)$', v)
                if exactValue:
                    # less than
                    fieldQ = self._build_q(k, '{}__lte', exactValue.groups()[0])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\>(.*)$', v)
                if exactValue:
                    # less than
                    fieldQ = self._build_q(k, '{}__gt', exactValue.groups()[0])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\|\>(.*)$', v)
                if exactValue:
                    # less than
                    fieldQ = self._build_q(k, '{}__gte', exactValue.groups()[0])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\"(.*)\"$', v)
                if exactValue:
                    # Exactly match
                    fieldQ = self._build_q(k, '{}', exactValue.groups()[0])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\[(.*)\]$', v)
                if exactValue:
                    # `in` operator
                    fieldQ = self._build_q(k, '{}__in', [i.strip() for i in exactValue.groups()[0].split(',')])
                    if not fieldQ:
                        continue
                    queryObj &= fieldQ
                    continue

                exactValue = re.match(r'^\~\[(.*)\]$', v)
                if exactValue:
                    # `not` operator
                    fieldQ = self._build_q(k, '{}__in', [i.strip() for i in exactValue.groups()[0].split(',')])
                    if not fieldQ:
                        continue
                    queryObj &= ~fieldQ
                    continue

                # Fuzzy match
                if self.ignoreCase:
                    fieldQ = self._build_q(k, '{}__icontains', v)
                else:
                    fieldQ = self._build_q(k, '{}__contains', v)
                if not fieldQ:
                    continue
                queryObj &= fieldQ
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
        :return Order by field name, if desc return [`-field`], if asc, return [`field`];
                if order by param not provided, then look for `default_order_by`
                if `default_order_by` is not provided, then return [`pk`] as default
        '''
        assert isinstance(requestParams, QueryDict), 'requestParams should be QueryDict'
        if 's' in requestParams.keys():
            value = requestParams['s']
            if value != '':
                m = re.search('(?<=-)\S+', value)
                if m:
                    # Desc
                    return ['-{}'.format(self.query_mapping[m.group()])]
                else:
                    # Asc
                    return [self.query_mapping[value]]

        # Default to user setting
        try:
            defaultOrderby = getattr(self, 'default_order_by')
            if len(defaultOrderby) == 0:
                return ['pk']
            else:
                return defaultOrderby
        except AttributeError:
            return ['pk']
