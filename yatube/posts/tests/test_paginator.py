from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='КБ')
        cls.user_follower = User.objects.create(username='follower')
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
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )
        cls.pages = {
            '?page=1': settings.NUM_OF_POSTS,
            '?page=2': settings.NUM_OF_POSTS_3
        }

    def setUp(self):
        self.client = Client()
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user_follower)

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
        for page_num, num_of_posts in self.pages.items():
            for value in url_names:
                with self.subTest(value=value):
                    response = self.client.get(value + page_num)
                    self.assertEqual(
                        len(
                            response.context['page_obj']
                        ), num_of_posts)

    def test_first_page_follow_index_contains(self):
        """Тест Пагинатора для 1й и 2й странцы для /follow_index/"""
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        for page_num, num_of_posts in self.pages.items():
            response = self.authorized_client_follower.get(
                reverse('posts:follow_index') + page_num
            )
            self.assertEqual(len(response.context['page_obj']), num_of_posts)
