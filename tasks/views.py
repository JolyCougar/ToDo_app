from django.http import JsonResponse
import json
from django.urls import reverse_lazy
from django.views.generic import ListView, View
from .models import Task
from django.contrib.auth.mixins import LoginRequiredMixin
from .tasks_mixins import EmailVerifiedMixin


class TaskView(EmailVerifiedMixin, ListView):
    model = Task
    template_name = 'index.html'
    context_object_name = 'task_list'
    login_url = reverse_lazy('my_auth:login')

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


class UpdateTaskView(View):
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            data = json.loads(request.body)
            task.complete = data.get('complete', False)
            task.save()
            return JsonResponse({'success': True, 'complete': task.complete})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})


class DeleteTaskView(View):
    def delete(self, request, task_id):
        try:
            task = Task.objects.get(pk=task_id)
            task.delete()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Задача не найдена.'})


class AddTaskView(View):
    def post(self, request):
        data = json.loads(request.body)
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return JsonResponse({'success': False, 'error': 'Название обязательны.'}, status=400)

        user = request.user

        task = Task.objects.create(user=user, name=name, description=description, complete=False)
        return JsonResponse({'success': True, 'task_id': task.id})
