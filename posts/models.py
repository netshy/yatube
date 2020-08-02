from django.db import models
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField

User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")

    class Meta:
        unique_together = ['user', 'author']

    def __str__(self):
        return str(self.id)


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = RichTextField()
    rules = RichTextField()

    def __str__(self):
        return str(self.title)


class Post(models.Model):
    text = RichTextField()
    pub_date = models.DateTimeField(verbose_name="Дата публикации", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author", db_index=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, related_name="group", blank=True, null=True,
                              db_index=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return str(self.id)

class Comment(models.Model):
    text = RichTextField()
    created = models.DateTimeField(verbose_name='Дата публикации', auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_comment', db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comment_post', db_index=True)

    def __str__(self):
        return str(self.text)
