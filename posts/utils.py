from django.shortcuts import redirect


def check_authentication(function):  # Проверка авторизованности пользователя, если не авторизован, то переадресация на index
    def check_value(request, *args, **kwargs):
        if request.user.is_authenticated:
            return function(request, *args, **kwargs)
        return redirect("index")

    return check_value
