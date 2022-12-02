from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='КБ')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='Тестовое описание'
        )

        cls.posts = Post.objects.bulk_create(
            [
                Post(
                    text=str(i) + ' Тестовый текст',
                    author=cls.user,
                    group=cls.group
                )
                for i in range(0, 13)
            ]
        )

    def test_first_page_contains(self):
        """Тест Пагинатора для 1й и 2й странцы"""
        url_names = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                args=[self.user]
            ),
        )
        pages = (
            ('?page=1', settings.NUM_OF_POSTS),
            ('?page=2', settings.NUM_OF_POSTS_3)
        )
        for page in pages:
            for value in url_names:
                with self.subTest(value=value):
                    response = self.client.get(value + page[0])
                    self.assertEqual(
                        len(
                            response.context['page_obj']
                        ), page[1])
