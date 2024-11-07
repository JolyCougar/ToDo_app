from django.utils import translation


def current_language(request):
    return {
        'current_language': translation.get_language()
    }
