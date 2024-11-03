from django.db.models import QuerySet
import logging
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
import json
from django.urls import reverse_lazy
from django.views.generic import ListView, View, TemplateView
from .models import Task
from .tasks_mixins import EmailVerifiedMixin

logger = logging.getLogger(__name__)


class TaskView(EmailVerifiedMixin, ListView):
    """
    Этот класс предоставляет список задач,
    связанных с текущим пользователем. Доступ к этому представлению
    разрешен только для пользователей с подтвержденным адресом электронной почты.
    """

    model = Task
    template_name = 'index.html'
    context_object_name = 'task_list'
    login_url = reverse_lazy('my_auth:login')

    def get_queryset(self) -> QuerySet[Task]:
        """
        Возвращает набор задач, связанных с текущим пользователем.

        :return: QuerySet задач пользователя.
        """

        return Task.objects.filter(user=self.request.user)


class UpdateTaskView(View):
    """
    Класс для обновления статуса задачи.

    Этот класс обрабатывает POST-запросы для обновления состояния задачи
    по заданному идентификатору. Он извлекает данные из тела запроса,
    обновляет поле 'complete' задачи и сохраняет изменения в базе данных.
    """

    def post(self, request, task_id) -> JsonResponse:
        """
        Обрабатывает обновление статуса задачи.

        :param request: HTTP запрос с данными для обновления статуса задачи.
        :param task_id: Идентификатор задачи, которую необходимо обновить.
        :return: JsonResponse с информацией об успехе операции и текущем статусе задачи
                 или сообщение об ошибке, если задача не найдена.
        """

        try:
            task = Task.objects.get(id=task_id)
            data = json.loads(request.body)
            task.complete = data.get('complete', False)
            task.save()
            logger.info(f'Задача с номером {task_id} у пользователя {request.user.id} выполнена ={task.complete}')
            return JsonResponse({'success': True, 'complete': task.complete})
        except Task.DoesNotExist:
            logger.error(f'Задача id {task_id} не найдена у пользователя {request.user.id}')
            return JsonResponse({'success': False, 'error': 'Task not found'})


class DeleteTaskView(View):
    """
    Класс для удаления задачи.

    Этот класс обрабатывает DELETE-запросы для удаления задачи
    по заданному идентификатору из базы данных.
    """

    def delete(self, request, task_id) -> JsonResponse:
        """
        Обрабатывает удаление задачи.

        :param request: HTTP запрос с данными для обновления удаления задачи.
        :param task_id: Идентификатор задачи, которую необходимо удалить.
        :return: JsonResponse с информацией об успехе операции и текущем статусе задачи
                 или сообщение об ошибке, если задача не найдена.
        """

        try:
            task = Task.objects.get(pk=task_id)
            task.delete()
            logger.info(f'Задача с номером {task_id} удалена у пользователя {request.user.id}')
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Задача не найдена.'})


class AddTaskView(View):
    """
    Класс для добавления задачи.

    Этот класс обрабатывает POST-запросы для добавления задачи
    извлекает название и описание задачи которые ввел пользователь,
     и добавляет в базу данных.
    """

    def post(self, request) -> JsonResponse:
        """
        Обрабатывает добавление задачи.

        :param request: HTTP запрос с данными для добавления задачи.
        :return: JsonResponse с информацией об успехе операции и текущем статусе задачи
                 или сообщение об ошибке, если задача не найдена.
        """

        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return JsonResponse({'success': False, 'error': 'Название обязательны.'}, status=400)

        user = request.user

        task = Task.objects.create(user=user, name=name, description=description, complete=False)
        logger.info(f'Добавлена новая задача {task.id} у пользователя {user.id}')
        return JsonResponse({'success': True, 'task_id': task.id})


class MainPageTask(TemplateView):
    """
    Класс для отображения главной страницы.

    Этот класс обрабатывает запросы к главной странице приложения.
    Если пользователь аутентифицирован, он будет перенаправлен на
    страницу задач. В противном случае будет отображена главная страница.
    """

    template_name = 'main.html'

    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        """
        Обрабатывает входящие запросы и выполняет перенаправление
        для аутентифицированных пользователей.

        :param request: HTTP запрос.
        :return: HttpResponse с перенаправлением на страницу задач
                 или ответом для отображения главной страницы.
        """

        if request.user.is_authenticated:
            logger.info(f'Пользователь {request.user.id} перенаправлен на станицу список задач')
            return redirect(reverse_lazy('task:task_view'))
        return super().dispatch(request, *args, **kwargs)
