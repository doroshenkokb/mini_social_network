from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
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
    if request.user.is_authenticated:
        following = username.following.exists()
        context = {
            'author': username,
            'page_obj': listsing(request, posts),
            'following': following,
        }
        return render(request, 'posts/profile.html', context)
    return render(
        request,
        'posts/profile.html',
        {
            'author': username,
            'page_obj': listsing(request, posts),
        }
    )


def post_detail(request, post_id):
    """Пост подробно"""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста."""
    form = PostForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            create_post = form.save(commit=False)
            create_post.author = request.user
            create_post.save()
            return redirect('posts:profile', create_post.author)
        return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Функция страницы редактирования постов."""
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'edit_post': True,
        'post_id': post_id,
    }
    return render(request, 'posts/create_post.html', context)


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
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
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
    follower = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and follower.exists():
        follower.delete()
    return redirect('posts:profile', username=username)
