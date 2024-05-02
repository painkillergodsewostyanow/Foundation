from django.urls.exceptions import Http404


def teacher_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_teacher():
                return view_func(request, *args, **kwargs)
        raise Http404()
    return _wrapped_view
