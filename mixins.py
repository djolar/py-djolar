# encoding: utf-8


class DjangoSearchMixin(object):
    '''
    Make the view class searchable
    '''
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
