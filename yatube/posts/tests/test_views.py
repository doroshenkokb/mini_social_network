import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='КБ')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        cache.clear()

    def context_ckeck(self, response, text, author, group):
        """Проверка контекста."""
        if 'page_obj' in response.context:
            post = response.context['page_obj'][0]
            self.assertEqual(post.text, text)
            self.assertEqual(post.author, author)
            self.assertEqual(post.group, group)
        else:
            post = response.context['post']
            self.assertEqual(post.text, text)
            self.assertEqual(post.author, author)
            self.assertEqual(post.group, group)

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
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
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
        )

    def test_create_show_and_post_edit_show_correct_context(self):
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

    def test_check_comment_can_use_only_authorized_client(self):
        """"Комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый коммент"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", kwargs={"post_id": self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text="Тестовый коммент"
            ).exists()
        )

    def test_follow_page(self):
        """"Проверка подписок."""
        # страница подписок пуста
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context["page_obj"]), 0)
        # подписка на автора поста
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        response_with_follow = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response_with_follow.context['page_obj']), 1)
        # подписка появилась у фоловера
        self.assertIn(self.post, response_with_follow.context["page_obj"])
        # пост отсутствует у обычного пользователя
        without_subscribes = User.objects.create(username='БезПодписок')
        self.authorized_client.force_login(without_subscribes)
        response_with_follow = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(self.post, response_with_follow.context['page_obj'])
        # отписка от автора
        Follow.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

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


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TaskPagesTests, cls).setUpClass()
        cls.user = User.objects.create_user(username='КБ')
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
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

    def test_image_in_index_and_profile_page(self):
        """Картинка передается на страницы
        /index/, /profile/, /group_list/ .
        """
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.post.author}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
        )
        for url in urls:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context['page_obj'][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        """Картинка передается на страницу post_detail."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        obj = response.context['post']
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        """Пост с картинкой создается в БД"""
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                image='posts/gifka.gif'
            ).exists()
        )
