from django.conf import settings
from django.core.paginator import Paginator


def listsing(request, posts):
    """Паджинатор по 10 постам."""
    paginator = Paginator(posts, settings.NUM_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
