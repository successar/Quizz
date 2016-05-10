from django.contrib.auth.decorators import login_required
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    user_model = get_user_model()
except ImportError:
    from django.contrib.auth.models import User
    user_model = User

from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ValidationError

from friendship.exceptions import AlreadyExistsError, AlreadyFriendsError
from friendship.models import Friend, FriendshipRequest
from django.views.generic import ListView, DeleteView

get_friendship_context_object_name = lambda: getattr(settings, 'FRIENDSHIP_CONTEXT_OBJECT_NAME', 'user')
get_friendship_context_object_list_name = lambda: getattr(settings, 'FRIENDSHIP_CONTEXT_OBJECT_LIST_NAME', 'users')


class view_friends(ListView):
    model = user_model
    template_name = 'friendship/friend/user_list.html'

    def get_queryset(self):
        user = self.request.user
        result = Friend.objects.friends(user)
        query = self.request.GET.get('q')
        
        if query:
            query = query.strip()
            result = result.filter(from_user__username__icontains=query)

        return result


@login_required
def friendship_add_friend(request, to_username, template_name='friendship/friend/add.html'):
    """ Create a FriendshipRequest """
    ctx = {'to_username': to_username}

    if request.method == 'POST':
        to_user = user_model.objects.get(username=to_username)
        from_user = request.user
        try:
            Friend.objects.add_friend(from_user, to_user)
        except ValidationError as e:
            ctx['errors'] = ["%s" % e]
        except AlreadyFriendsError as e:
            ctx['errors'] = ["%s" % e]
        except AlreadyExistsError as e:
            ctx['errors'] = ["%s" % e]
        else:
            return redirect('friendship_view_users')

    return render(request, template_name, ctx)


@login_required
def friendship_accept(request, friendship_request_id):
    """ Accept a friendship request """
    if request.method == 'POST':
        f_request = get_object_or_404(request.user.friendship_requests_received, id=friendship_request_id)
        f_request.accept()
        return redirect('friendship_view_friends')

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


@login_required
def friendship_reject(request, friendship_request_id):
    """ Reject a friendship request """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_received,
            id=friendship_request_id)
        f_request.reject()
        return redirect('friendship_request_list')

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


@login_required
def friendship_cancel(request, friendship_request_id):
    """ Cancel a previously created friendship_request_id """
    if request.method == 'POST':
        f_request = get_object_or_404(
            request.user.friendship_requests_sent,
            id=friendship_request_id)
        f_request.cancel()
        return redirect('friendship_request_list')

    return redirect('friendship_requests_detail', friendship_request_id=friendship_request_id)


@login_required
def friendship_request_list(request, template_name='friendship/friend/requests_list.html'):
    """ View unread and read friendship requests """
    # friendship_requests = Friend.objects.requests(request.user)
    friendship_requests = FriendshipRequest.objects.filter(rejected__isnull=True, to_user=request.user)

    return render(request, template_name, {'requests': friendship_requests})


@login_required
def friendship_request_list_rejected(request, template_name='friendship/friend/requests_list.html'):
    """ View rejected friendship requests """
    # friendship_requests = Friend.objects.rejected_requests(request.user)
    friendship_requests = FriendshipRequest.objects.filter(rejected__isnull=True)

    return render(request, template_name, {'requests': friendship_requests})


@login_required
def friendship_requests_detail(request, friendship_request_id, template_name='friendship/friend/request.html'):
    """ View a particular friendship request """
    f_request = get_object_or_404(FriendshipRequest, id=friendship_request_id)

    return render(request, template_name, {'friendship_request': f_request})


class all_users(ListView):
    model = user_model
    template_name = 'friendship/user_actions.html'

    def get_queryset(self):
        result = super(all_users, self).get_queryset().exclude(id=self.request.user.id)
        query = self.request.GET.get('q')
        if query:
            query = query.strip()

        if query:
            result = result.filter(username__icontains=query)
        else:
            result = result.none()

        return result

    def get_context_data(self, **kwargs):
        context = super(all_users, self).get_context_data(**kwargs)
        friends = Friend.objects.friends(self.request.user).values_list('from_user', flat=True)
        context['friends'] = friends
        return context


def remove_friend(request, to_username):
    to_user = user_model.objects.get(username=to_username)
    from_user = request.user
    Friend.objects.remove_friend(from_user, to_user)
    return redirect('friendship_view_friends')