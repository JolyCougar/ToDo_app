from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
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

