from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings


class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        language = request.session.get('django_language')

        if language:
            translation.activate(language)
        else:
            accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if accept_language:
                language = accept_language.split(',')[0].split(';')[0]
                if language in dict(settings.LANGUAGES):
                    translation.activate(language)
                    request.session['django_language'] = language
                else:
                    translation.activate(settings.LANGUAGE_CODE)
            else:
                translation.activate(settings.LANGUAGE_CODE)
