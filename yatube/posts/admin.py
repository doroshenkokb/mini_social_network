from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    """
    Информация о созданных постах
    """

    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """
    Информация о созданных группах
    """

    list_display = (
        'pk',
        'description',
        'title',
        'slug',
    )

    search_fields = ('author',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text', 'created')
    list_filter = ('created', 'author')
    search_fields = ('author', 'email', 'text')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
