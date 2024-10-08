from django.http import JsonResponse
import json
from django.views.generic import ListView, View
from .models import Task


class TaskView(ListView):
    model = Task
    queryset = Task.objects.all()
    template_name = 'index.html'


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
