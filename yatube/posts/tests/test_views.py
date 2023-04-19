import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='КБ')
        cls.user_follower = User.objects.create(username='follower')
        cls.user_2 = User.objects.create_user(username='user_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.gif_ka = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='gifka.gif',
            content=cls.gif_ka,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def context_ckeck(self, response, text, author, group, image):
        """Проверка контекста."""
        post = (
            response.context['page_obj'][0] 
            if 'page_obj' in response.context 
            else response.context['post']
        )
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)
        self.assertEqual(post.image, image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
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
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:follow_index'
            ): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_show_correct_context(self):
        """
        Проверка контекста шаблона /group_list/.
        """
        response = self.guest_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )
        )
        self.context_ckeck(
            response,
            self.post.text,
            self.post.author,
            self.post.group,
            self.post.image,
        )
        self.assertEqual(response.context['group'], self.group)

    def test_profile_show_correct_context(self):
        """
        Проверка контекста шаблона /profile/.
        """
        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user}
            )
        )
        self.context_ckeck(
            response,
            self.post.text,
            self.post.author,
            self.post.group,
            self.post.image,
        )
        self.assertEqual(response.context['author'], self.user)

    def test_index_show_correct_context(self):
        """
        Проверка контекста шаблона /index/.
        """
        response = self.guest_client.get(reverse('posts:index'))
        self.context_ckeck(
            response,
            self.post.text,
            self.post.author,
            self.post.group,
            self.post.image,
        )

    def test_follow_index_show_correct_context(self):
        """
        Проверка контекста шаблона /follow_index/.
        """
        response = self.authorized_client_follower.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.context_ckeck(
            response,
            self.post.text,
            self.post.author,
            self.post.group,
            self.post.image,
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.context_ckeck(
            response,
            self.post.text,
            self.post.author,
            self.post.group,
            self.post.image,
        )

    def test_create__and_post_edit_show_correct_context(self):
        """Шаблоны post_edit и create сформированы с правильным контекстом."""
        urls = (
            reverse(
                'posts:post_create'
            ),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                for url in urls:
                    form_field = self.authorized_client.get(
                        url
                    ).context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверка создания поста на страницах с выбранной группой"""
        form_fields = {
            reverse(
                'posts:index'
            ): self.post,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): self.post,
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): self.post,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """
        Проверка чтобы созданный пост не попал в группу,
        для которой не был предназначен.
        """
        group = Group.objects.create(
            title='Тестовая группа#2',
            slug='test-slug#2',
            description='Тестовое описание#2',
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост2',
            group=group
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            )
        )
        self.assertNotIn(post, response.context['page_obj'])

    def test_follow(self):
        """Тесты на подписку."""
        self.authorized_client_follower.get(
            reverse(
                'posts:profile_follow', kwargs={'username': self.user}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=self.user,
                user=self.user_follower,
            ).exists(),
        )

    def test_unfollow(self):
        """Тесты на отписку."""
        self.authorized_client_2.get(
            reverse(
                'posts:profile_unfollow', kwargs={'username': self.user}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.user,
                user=self.user_2
            ).exists()
        )

    def test_follow_index(self):
        """
        Проверка что новая запись пользователя появляется
        в ленте тех, кто на него подписан и
        не появляется в ленте тех, кто не подписан.
        """
        response_follower = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        post_follow = response_follower.context.get('page_obj')[0]
        response_unfollower = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        post_unfollow = response_unfollower.context.get('page_obj')
        self.assertEqual(post_follow, self.post)
        self.assertEqual(post_unfollow.object_list.count(), 0)

    def test_cache_index(self):
        """Проверка хранения и очистка кэша."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Тестовый текст',
            author=self.post.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)
