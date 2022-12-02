from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.user_non_author = User.objects.create(username='Noname')
        self.user = User.objects.create(username='КБ')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        self.urls = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ),
            '/unexisting_page/',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized__non_author = Client(PostURLTests.user_non_author)
        self.authorized__non_author.force_login(PostURLTests.user_non_author)
        self.authorized_client = Client(PostURLTests.user)
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны всем пользователям."""
        for url in self.urls:
            with self.subTest(url):
                if url == '/unexisting_page/':
                    response = self.guest_client.get('/unexisting_page/')
                    self.assertEqual(
                        response.status_code,
                        HTTPStatus.NOT_FOUND
                    )
                else:
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_posts_post_edit_url_exists_at_author(self):
        """Страницы /posts/post_id/edit/ доступна только автору"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_authorized__non_author(self):
        """
        Редирект /posts/post_id/edit/ не автора
        """
        response = self.authorized__non_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ), follow=True
        )
        self.assertRedirects(response, '/posts/1/')

    def test_creat_url_exists_at_author_and_authorized_client(self):
        """
        Страница /create/ доступна авторизированному пользователю и автору.
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_creat_edit_url_redirect_anonymous_on_auth_login(self):
        """
        Редирект с /create/
         не авторизованного пользователя.
        """
        response = self.guest_client.get(
            reverse(
                'posts:post_create'
            ), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_anonymous_on_auth_login(self):
        """
        Редирект с /posts/post_id/edit/ не
        авторизованнова пользователя.
        """
        response = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')

    def test_post_comment_redirect_anonymous_on_auth_login(self):
        """
        Редирект с /posts/post_id/comment/ не
        авторизованнова пользователя.
        """
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            follow=True,
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон(Общедоступные)."""
        self.templates_url_names_all_users = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',

            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
        }
        for url, template in self.templates_url_names_all_users.items():
            cache.clear()
            with self.subTest(template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_create_post_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон(create_post)."""
        self.templates_url_names_auth = {
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
        }
        for url, template in self.templates_url_names_auth.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
