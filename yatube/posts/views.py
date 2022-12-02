from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import listsing

User = get_user_model()


@cache_page(20 * 15)
def index(request):
    """Главная страница."""
    posts = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': listsing(request, posts)
    }
    return render(request, 'posts/index.html', context)


def group_post(request, slug):
    """Посты, отфильтрованные по группам."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author')
    context = {
        'group': group,
        'page_obj': listsing(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Профиль пользователя."""
    username = get_object_or_404(User, username=username)
    posts = username.posts.select_related('author', 'group')
    following = username.following.exists()
    context = {
        'author': username,
        'page_obj': listsing(request, posts),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Пост подробно"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста."""
    user = request.user
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None
        )
        if form.is_valid():
            form = form.save(commit=False)
            form.author = user
            form.save()
            return redirect('posts:profile', user)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    context = {
        'form': form,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Редактироание поста."""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,

    )
    if request.method == 'POST':
        if form.is_valid:
            form.save()
            return redirect(f'/posts/{post_id}/')
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Комментирование поста."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Посты авторов, на которых подписан пользователь."""
    follower = Follow.objects.filter(user=request.user).values_list(
        "author_id", flat=True
    )
    posts = Post.objects.filter(author_id__in=follower)
    context = {
        'title': 'Подписки',
        'page_obj': listsing(request, posts),
    }
    template = 'posts/follow.html'
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписка."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    """Отписка."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect("posts:follow_index")
