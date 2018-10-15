#encoding: utf-8
"""
Djolar searcher mixins
"""


class DjangoSearchMixin(object):
    '''
    Make the view class searchable
    '''
    searcher_class = None

    def get_searcher_class(self):
        """
        Return the class to use for the search.
        Defaults to using `self.searcher_class`.
        """
        assert self.searcher_class is not None, (
            "'%s' should either include a `searcher_class` attribute, "
            "or override the `get_searcher_class()` method."
            % self.__class__.__name__
        )

        return self.searcher_class

    def get_searcher(self, *args, **kwargs):
        '''
        Return the search instance for building model search query object
        '''
        searcher_class = self.get_searcher_class()
        return searcher_class(*args, **kwargs)

    def get_search_queryset(self, *args, **kwargs):
        '''
        Return the queryset for result filter
        '''
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_search_queryset()` method."
            % self.__class__.__name__
        )

        return self.queryset

    def get_queryset(self, *args, **kwargs):
        searcher = self.get_searcher()

        # Build search field
        queryQ = searcher.get_query_fields(self.request.GET)

        # Get order by field
        orderBy = searcher.get_order_fields(self.request.GET)

        # Make queryset
        queryset = self.get_search_queryset().filter(queryQ).order_by(*orderBy)

        return queryset

