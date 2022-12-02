from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """
      Форма создания поста.
    """
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение'
        }


class CommentForm(forms.ModelForm):
    """
    Форма добавления комментария.
    """
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария',
        }
