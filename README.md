# djolar
A simple and light weight model search module for django, easy to connect front-end to backend

Why we need djolar
--------------

Performing search on the django model is little bit difficule when your front-end app needs complicated and flexible search function.
Consider the book and author case, suppose we have modle definition `Book`, and `Author` as below:

```python
class Author(models.Model):
    name = models.CharField('name of the author', max_length=50)
    age = models.IntegerField('age')

class Book(models.Model):
    name = models.CharField('name of the book', max_length=100)
    publish_at = models.DateTimeField('publish date')
    author = models.ForeignKey(Author)
```

And we need to implement a search engine in the front-end web app to support `Book` search
Search criteria would be like tis:

* search by book name (contains)
* search by book name (exactly match)
* search by author name
* search by the book's author's age
* search by the book publish date range
* search critiera with the combination above.

So how can we meet the requirement above with django? You may begin thinking using serveral `filter` chain to perform the search, and the code may look this this:

```python
queryset = Book.objects.all()

if request.GET.get('name'):
    queryset = queryset.filter(name=request.GET['name'])

if request.GET.get('author'):
    queryset = queryset.filter(author__name=request.GET['author'])

if request.GET.get('age'):
    queryset = queryset.filter(author__name=request.GET['age'])

if request.GET.get('from'):
    queryset = queryset.filter(publish_at__gte=request.GET['from'])
    
if request.GET.get('to'):
    queryset = queryset.filter(publish_at__lte=request.GET['to'])

return queryset
```

Wow... it is really complicated.. But hold on, how can you support `exactly match` with book name? How did you write the query string? It is really a problem, isn't it?

So it is `djolar` show time....

Usage
--------

`djolar` is making use of `Q` to build a compilicated filter criteria. It is very flexible to handle filter with `Q`.

To use `djolar`, you just need to implement two things:

1. create a subclass of `DjangoSearchParser`. And defining the front-end query param field name and model field name mapping.
2. use correct `djolar` syntax to write a custom query param string.

Query param syntax
-----------------

All query field name value pair should be encoded and assign to `q` field name as below:

        q=key1:value1+key2:value2+key3:value3&s=order&extrafield=value
        
The above string indicate we need to search with 3 name value pairs:

```
(key1, value1)
(key2, value2)
(key3, value3)
```

The search syntax would be like this:

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

Example
-------

Firstly, we just need to subclass `DjangoSearchParser` to define a book search parser to help `djolar` to do query param and model field name mapping. The mapping is useful when you don't want to expose the django model field name to the front-end.

Suppose, the query param from front-end contains the following field names:

* `name` represent the name of the book
* `author` represent the author name of the book
* `from` represent the publish date range begin date
* `to` represent the publish date range end date

So the parser may look like this:

```python

from parser import DjangoSearchParser

class BookSearchParser(DjangoSearchParser):
    query_mapping = {
        'name': 'name',
        'age': 'author__age',
        'author': 'author__name',
        'from': 'publish_at__gte',
        'to': 'publish_at__lte',
    }
```

Then we can use the `BookSearchParser` to parse the query string send from front-end:

```python
import urllib

# Search by book name CONTAINS Programming, and the author name CONTAINS Dennis Ritchie
# We need to encode the param to ensure no conflict.
queryParam = '?q=' + urllib.quote('name:Programming+author:Dennis Ritchie')
queryParam = '?q=name%3AThe%20C%20Programming%20Language%2Bauthor%3ADennis%20Ritchie'

# Create a parser
parser = BookSearchParser()

# Parse the queryParam, and get an `Q` object
queryQ = parser.get_query_fields(queryParam)

# Perform filter
results = Book.objects.filter(queryQ)
```

Now you can change the queryParam as you need to perform more complicated search

```python

>>> queryParam = '?q=' + urllib.quote('name:Programming+author:Dennis Ritchie+from:2016-01-01+to:2016-12-31')
>>> print queryParam
'?q=name%3AProgramming%2Bauthor%3ADennis%20Ritchie%2Bfrom%3A2016-01-01%2Bto%3A2016-12-31'

# Parse
queryQ = parser.get_query_fields(queryParam)

# Search 
# Result with: 
#    1. Book name contains 'Programming', AND
#    2. author name contains 'Dennis Ritchie' AND
#    3. publish from 2016-01-01 to 2016-12-31
results = Book.objects.filter(queryQ)
```

More examples
------------

Contains operator, like the SQL `LIKE` concept

```python
# Book name contains python (case ignore)
queryQ = searcher.get_query_fields(QueryDict('q=name:Python'))
```

Exactly match operator, like SQL `=`

```python
# Book name equal to Python (case ignore)
queryQ = searcher.get_query_fields(QueryDict('q=name:"Python"'))
```

IN operator, like SQL `in`

```python
# Book name in one of these values ('Python', 'Ruby', 'Swift')
queryQ = searcher.get_query_fields(QueryDict('q=name:[Python,Ruby,Swift]'))
```
NOT operator, LIKE SQL `NOT IN`

```python
# Book name NOT in these values ('Python', 'Ruby', 'Swift')
queryQ = searcher.get_query_fields(QueryDict('q=name:~[Python,Ruby,Swift]'))
```

Less than, LIKE SQL `<`

```python
# Author age less than 18
queryQ = searcher.get_query_fields(QueryDict('q=age<18'))
```

Less than or equal to, LIKE SQL `<=`

```python
# Author age less or equal to 18
queryQ = searcher.get_query_fields(QueryDict('q=age|<18'))
```


Greater than, LIKE SQL `>`

```python
# Author age greater than 18
queryQ = searcher.get_query_fields(QueryDict('q=age>18'))
```

Greater than or equal to, LIKE SQL `>=`

```python
# Author age greater than or equal to 18
queryQ = searcher.get_query_fields(QueryDict('q=age|>18'))
```

After getting the queryQ object, you can filter the Model or extend it more as you need

```python
Book.objects.filter(queryQ)

Book.objects.filter(queryQ).filter(pk__gte=1)

Book.objects.filter(queryQ | Q(pk__gte=1))
```


Implement with DJANGO & DJANGO RESET FRAMEWORK
----------------------------------------------


```python

class APIBookSearcher(DjangoSearchParser):
    query_mapping = {
        'from': 'createDate__gte',
        'to': 'createDate__lte',
    }

    force_search = {
        'status__in': ('published', 'in progress')
    }

    # Default to filter 7 days sales
    default_search = {
        'createDate__range': (timedelta(days=-7) + now(), now())
    }
    

class APIBookListView(mixins.ListModelMixin, 
                      DjangoSearchMixin,
                      generics.GenericAPIView):
    '''
    Book list API
    '''
    serializer_class = APIReportXYNumericDataSerializer
    searcher_class = APIBookSearcher

    def get(self, request, *args, **kwargs):
        self.check_permissions(request)

        # Get search parameters
        searcher = self.get_searcher()
        queryQ = searcher.get_query_fields(self.request.GET)
        
        # Get order by field
        orderBy = searcher.get_order_fields(self.request.GET)

        queryset = Order.objects.filter(queryQ).order_by(**orderBy)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```
