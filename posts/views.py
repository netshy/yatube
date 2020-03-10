from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


def index(request):
    post_list = Post.objects.select_related().order_by(
        "-pub_date"
    ).annotate(
        comment_count=Count('comment_post')
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', context={'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.select_related().filter(
        group=group
    ).order_by(
        "-pub_date"
    ).annotate(
        comment_count=Count('comment_post')
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    return render(request, "group.html", context={
        "group": group,
        "page": page,
        'paginator': paginator,
    })


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES)

        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author_id = request.user.id
            new_post.save()
            return redirect("index")

        return render(request, "post_new.html", context={"form": form})

    form = PostForm()
    return render(request, "post_new.html", context={"form": form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_count = Post.objects.select_related().filter(author=user.pk).count()
    post_list = Post.objects.select_related().filter(
        author=user.pk
    ).order_by(
        "-pub_date"
    ).annotate(
        comment_count=Count('comment_post')
    )

    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    following_count = Follow.objects.filter(author=user).count()
    follower_count = Follow.objects.filter(user=user).count()

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=user).first()

        return render(request, "profile.html", context={
            "profile": user,
            "post_count": post_count,
            "page": page,
            'paginator': paginator,
            'following': following,
            'following_count': following_count,
            'follower_count': follower_count,
        })

    return render(request, "profile.html", context={
        "profile": user,
        "post_count": post_count,
        "page": page,
        'paginator': paginator,
        'following_count': following_count,
        'follower_count': follower_count,
    })


def post_view(request, username, post_id):
    user = get_object_or_404(User, username=username)
    post_count = Post.objects.select_related().filter(author=user.pk).count()
    post = get_object_or_404(Post, author=user.pk, id=post_id)

    comments = Comment.objects.select_related().filter(post=post_id)
    form = CommentForm()

    following_count = Follow.objects.filter(author=user).count()
    follower_count = Follow.objects.filter(user=user).count()

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=user).first()
        return render(request, "post.html", context={
            "profile": user,
            "post_count": post_count,
            "post": post,
            "form": form,
            "comments": comments,
            'following': following,
            'following_count': following_count,
            'follower_count': follower_count,
        })

    return render(request, "post.html", context={
        "profile": user,
        "post_count": post_count,
        "post": post,
        "form": form,
        "comments": comments,
        'following_count': following_count,
        'follower_count': follower_count,
    })


@login_required
def post_edit(request, username, post_id):
    if request.user.username != username:
        return redirect("post", username, post_id)

    author_post = get_object_or_404(Post, id=post_id)
    if author_post.author_id == request.user.id:
        bound_form = PostForm(request.POST or None, files=request.FILES or None, instance=author_post)

        if request.method == "POST":

            if bound_form.is_valid():
                bound_form.save()
                return redirect("post", username, post_id)

            return render(request, "edit.html", context={"form": bound_form})

        return render(request, "edit.html", context={"form": bound_form, 'post': author_post})

    return redirect("post", username, post_id)


@login_required
def add_comment(request, username, post_id):
    if request.user.is_authenticated:
        post = get_object_or_404(Post, id=post_id)
        form = CommentForm(request.POST or None)

        if request.method == 'POST':
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect("post", username, post_id)

        return redirect("post", username, post_id)

    return redirect("post", username, post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).count()
    if follow == 0:
        page = []  # для сдачи тестов
        return render(request, "follow.html", {'page': page})

    post_list = Post.objects.select_related().order_by(
        "-pub_date"
    ).filter(
        author__following__user=request.user
    ).annotate(
        comment_count=Count('comment_post')
    )
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    if request.user.username != username:
        author = User.objects.get(username=username)
        Follow.objects.create(user=request.user, author=author)
        return redirect('profile', username)
    return redirect('profile', username)



@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('profile', username)
