from djolar.parser import DjangoSearchParser
from django.test import TestCase
from django.http.request import QueryDict


class TestDjangoSearchParser(TestCase):

    class CustomDjangoSearchParser(DjangoSearchParser):
        query_mapping = {
            'st': 'status',
        }
        default_order_by = ['-pk']

    def setUp(self):
        self.searcher = self.CustomDjangoSearchParser()

    def testGetQueryFields(self):
        # Test `contains`
        q = self.searcher.get_query_fields(QueryDict('q=st__co__submitted'))
        self.assertEqual(q.children[0][0], 'status__icontains')
        self.assertEqual(q.children[0][1], 'submitted')

        q = self.searcher.get_query_fields(QueryDict('q=st:'))
        self.assertEqual(len(q.children), 0)

        # Test exactly match
        q = self.searcher.get_query_fields(QueryDict('q=st__eq__submitted'))
        self.assertEqual(q.children[0][0], 'status')
        self.assertEqual(q.children[0][1], 'submitted')

        # Test `in` operator
        q = self.searcher.get_query_fields(QueryDict('q=st__in__[v1,v2,v3]'))
        self.assertEqual(q.children[0][0], 'status__in')
        self.assertEqual(q.children[0][1], ['v1', 'v2', 'v3'])

        # Test `not` operator
        q = self.searcher.get_query_fields(QueryDict('q=st__ni__[value1,value2,value3]'))
        self.assertEqual(q.negated, True)
        self.assertEqual(q.children[0][0], 'status__in')
        self.assertEqual(q.children[0][1], ['value1', 'value2', 'value3'])


class TestDjangoSearchParserWithDefault(TestCase):
    class CustomDefaultSearcher(DjangoSearchParser):
        query_mapping = {
            'st': 'status'
        }
        default_search = {
            'name__eq': 'abc'
        }

    def setUp(self):
        self.searcher = self.CustomDefaultSearcher()

    def testDefaultSearchWithEmptyParam(self):
        q = self.searcher.get_query_fields(QueryDict(''))
        self.assertEqual(q.connector, u'AND')
        self.assertEqual(q.children[0][0], 'name__eq')
        self.assertEqual(q.children[0][1], 'abc')

    def testDefaultSearchWithSearchParam(self):
        q = self.searcher.get_query_fields(QueryDict('q=st__co__aaa'))
        self.assertEqual(q.connector, u'AND')
        self.assertEqual(q.children[0][0], 'status__icontains')
        self.assertEqual(q.children[0][1], 'aaa')


class TestDjangoSearchParserWithForceSearch(TestCase):
    class CustomDefaultSearcher(DjangoSearchParser):
        query_mapping = {
            'st': 'status'
        }
        force_search = {
            'name__eq': 'abc'
        }

    def setUp(self):
        self.searcher = self.CustomDefaultSearcher()

    def testDefaultSearchWithEmptyParam(self):
        q = self.searcher.get_query_fields(QueryDict(''))
        self.assertEqual(q.connector, u'AND')
        self.assertEqual(q.children[0][0], 'name__eq')
        self.assertEqual(q.children[0][1], 'abc')

    def testDefaultSearchWithSearchParam(self):
        q = self.searcher.get_query_fields(QueryDict('q=st__co__aaa'))
        self.assertEqual(q.connector, u'AND')
        self.assertEqual(q.children[0][0], 'name__eq')
        self.assertEqual(q.children[0][1], 'abc')
        self.assertEqual(q.children[1][0], 'status__icontains')
        self.assertEqual(q.children[1][1], 'aaa')


class TestDjangoSearchParserWithList(TestCase):

    class CustomSearchParser(DjangoSearchParser):
        query_mapping = {
            'st': ['product_status', 'status']
        }

    class CustomDjangoSearchParserCaseSensitive(DjangoSearchParser):
        query_mapping = {
            'st': ['product_status', 'status']
        }
        ignore_case = False

    def setUp(self):
        self.searcher = self.CustomSearchParser()
        self.sensitiveSearcher = self.CustomDjangoSearchParserCaseSensitive()

    def testGetQueryFields(self):
        # Test `contains`
        q = self.searcher.get_query_fields(QueryDict('q=st__co__submitted'))
        self.assertEqual(q.connector, 'OR')
        self.assertEqual(q.children[0][0], 'product_status__icontains')
        self.assertEqual(q.children[0][1], 'submitted')
        self.assertEqual(q.children[1][0], 'status__icontains')
        self.assertEqual(q.children[1][1], 'submitted')

        q = self.searcher.get_query_fields(QueryDict('q=st:'))
        self.assertEqual(len(q.children), 0)

        # Test exactly match
        q = self.searcher.get_query_fields(QueryDict('q=st__eq__submitted'))
        self.assertEqual(q.connector, 'OR')
        self.assertEqual(q.children[0][0], 'product_status')
        self.assertEqual(q.children[0][1], 'submitted')
        self.assertEqual(q.children[1][0], 'status')
        self.assertEqual(q.children[1][1], 'submitted')

        # Test `in` operator
        q = self.searcher.get_query_fields(QueryDict('q=st__in__[v1,v2,v3]'))
        self.assertEqual(q.connector, 'OR')
        self.assertEqual(q.children[0][0], 'product_status__in')
        self.assertEqual(q.children[0][1], ['v1', 'v2', 'v3'])
        self.assertEqual(q.children[1][0], 'status__in')
        self.assertEqual(q.children[1][1], ['v1', 'v2', 'v3'])

        # Test `not` operator
        q = self.searcher.get_query_fields(QueryDict('q=st__ni__[v1,v2,v3]'))
        self.assertTrue(q.negated)
        self.assertEqual(q.children[0].connector, u'OR')
        self.assertEqual(q.children[0].children[0][0], 'product_status__in')
        self.assertEqual(q.children[0].children[0][1], ['v1', 'v2', 'v3'])
        self.assertEqual(q.children[0].children[1][0], 'status__in')
        self.assertEqual(q.children[0].children[1][1], ['v1', 'v2', 'v3'])


class TestDjangoSearchParserWithCompare(TestCase):

    class CustomDjangoSearchParser(DjangoSearchParser):
        query_mapping = {
            'st': 'status',
        }
        default_order_by = ['-pk']

    def setUp(self):
        self.searcher = self.CustomDjangoSearchParser()

    def testGetQueryFields(self):
        # Test `lt`
        q = self.searcher.get_query_fields(QueryDict('q=st__lt__submitted'))
        self.assertEqual(q.children[0][0], 'status__lt')
        self.assertEqual(q.children[0][1], 'submitted')

        q = self.searcher.get_query_fields(QueryDict('q=st__lte__submitted'))
        self.assertEqual(q.children[0][0], 'status__lte')
        self.assertEqual(q.children[0][1], 'submitted')

        q = self.searcher.get_query_fields(QueryDict('q=st__gt__submitted'))
        self.assertEqual(q.children[0][0], 'status__gt')
        self.assertEqual(q.children[0][1], 'submitted')

        q = self.searcher.get_query_fields(QueryDict('q=st__gte__submitted'))
        self.assertEqual(q.children[0][0], 'status__gte')
        self.assertEqual(q.children[0][1], 'submitted')


class TestDjangoSearchParserSorting(TestCase):
    class CustomDjangoSearchParser(DjangoSearchParser):
        query_mapping = {
            'st': 'status',
            'n': 'name',
        }
        default_order_by = ['status']

    class CustomDjangoSearchParserWithoutSort(DjangoSearchParser):
        query_mapping = {
            'st': 'status',
            'n': 'name',
        }

    def setUp(self):
        self.searcher = self.CustomDjangoSearchParser()
        self.searcher_nosort = self.CustomDjangoSearchParserWithoutSort()

    def testGetSortField(self):
        # Test empty sort param
        s = self.searcher.get_order_fields(QueryDict('q=st__lt__submitted&s='))
        self.assertEqual(set(s), set(['status']))

        # Test `sort` by decending
        s = self.searcher.get_order_fields(QueryDict('q=st__lt__submitted&s=-n'))
        self.assertEqual(set(s), set(['-name']))

        # Test sort by asc
        s = self.searcher.get_order_fields(QueryDict('q=st__lt__submitted&s=n'))
        self.assertEqual(set(s), set(['name']))

        # Test sort not provided, by default_order_by is provided
        s = self.searcher.get_order_fields(QueryDict('q=st__lt__submitted'))
        self.assertEqual(set(s), set(['status']))

    def testGetSortFieldWithoutDefaultSort(self):
        # Test no sort param given
        s = self.searcher_nosort.get_order_fields(QueryDict('q=st__eq__submitted'))
        self.assertEqual(set(s), set(['pk']))

        # Test empty sort param
        s = self.searcher_nosort.get_order_fields(QueryDict('q=st__lt__submitted&s='))
        self.assertEqual(set(s), set(['pk']))
