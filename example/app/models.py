from django.db import models


class Author(models.Model):
    name = models.CharField('name of the author', max_length=50)
    age = models.IntegerField('age')

class Book(models.Model):
    name = models.CharField('name of the book', max_length=100)
    publish_at = models.DateTimeField('publish date')
    author = models.ForeignKey(Author)
    status = models.CharField('status of the book', max_length=10)
    createDate = models.DateTimeField('create at', auto_now=True)

