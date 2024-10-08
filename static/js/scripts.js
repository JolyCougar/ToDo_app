const dateDisplay = document.getElementById('dateDisplay');
const incompleteCount = document.getElementById('incompleteCount');
const taskList = document.getElementById('taskList');
const completedList = document.getElementById('completedList');
const cookieBanner = document.getElementById('cookieBanner');
const acceptCookiesButton = document.getElementById('acceptCookies');
const toggleCompletedListButton = document.getElementById('toggleCompletedList');
const addTaskButton = document.getElementById('addTaskButton');
const taskInput = document.getElementById('taskInput');
const taskDescription = document.getElementById('taskDescription');
const modal = document.getElementById('modal');
const closeModal = document.getElementById('closeModal');
const confirmAddTask = document.getElementById('confirmAddTask');

// Устанавливаем текущую дату
const currentDate = new Date();
dateDisplay.textContent = currentDate.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
});

// Инициализация счетчика невыполненных задач
updateIncompleteCount();

// Обработчики событий
acceptCookiesButton.addEventListener('click', hideCookieBanner);
toggleCompletedListButton.addEventListener('click', toggleCompletedList);
addTaskButton.addEventListener('click', showModal);
closeModal.addEventListener('click', hideModal);
window.addEventListener('click', hideModalOnClickOutside);
document.getElementById('taskForm').addEventListener('submit', addTask);
taskList.addEventListener('change', handleTaskChange);
taskList.addEventListener('click', handleDeleteTask);
completedList.addEventListener('click', handleDeleteTask);

// Функции
function hideCookieBanner() {
    cookieBanner.style.display = 'none';
}

function toggleCompletedList() {
    const isHidden = completedList.classList.contains('show');
    if (isHidden) {
        completedList.classList.remove('show'); // Убираем класс для скрытия
        toggleCompletedListButton.textContent = 'Развернуть';
    } else {
        completedList.classList.add('show'); // Добавляем класс для показа
        toggleCompletedListButton.textContent = 'Свернуть';
    }
}

function showModal() {
    modal.style.display = 'flex';
    taskInput.focus();
}

function hideModal() {
    modal.style.display = 'none';
}

function hideModalOnClickOutside(event) {
    if (event.target === modal) {
        hideModal();
    }
}

function addTask(event) {
    event.preventDefault();
    const taskName = taskInput.value.trim();
    const taskDescriptionText = taskDescription.value.trim();

    if (!taskName) {
        alert('Пожалуйста, заполните название задачи.');
        return;
    }

    fetch('/add-task/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({name: taskName, description: taskDescriptionText})
    })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                addTaskToDOM(data.task_id, taskName, taskDescriptionText);
                taskInput.value = '';
                taskDescription.value = '';
                hideModal();
                updateIncompleteCount();
            } else {
                alert('Ошибка добавления задачи: ' + data.error);
            }
        })
        .catch(handleError);
}

function handleResponse(response) {
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    return response.json();
}

function handleError(error) {
    console.error('Ошибка:', error);
    alert('Произошла ошибка. Пожалуйста, попробуйте еще раз.');
}

function addTaskToDOM(taskId, taskName, taskDescriptionText) {
    const newTaskItem = createTaskElement(taskId, taskName, taskDescriptionText);
    taskList.appendChild(newTaskItem);
}

function createTaskElement(taskId, taskName, taskDescriptionText) {
    const taskItem = document.createElement('li');
    taskItem.className = 'task-item';
    taskItem.setAttribute('data-task-id', taskId);
    taskItem.innerHTML = `
        <input type="checkbox" id="task${taskId}" complete="false">
        <label for="task${taskId}">${taskName}</label>
        <span class="task-details">
            <span>${taskDescriptionText}</span>
        </span>
        <button class="delete-task" aria-label="Удалить задачу">🗑️</button>
    `;
    return taskItem;
}

function updateIncompleteCount() {
    const checkboxes = taskList.querySelectorAll('input[type="checkbox"]');
    const completedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;
    incompleteCount.textContent = checkboxes.length - completedCount; // Обновляем текст счетчика
}

function handleTaskChange(event) {
    if (event.target.type === 'checkbox') {
        const taskItem = event.target.closest('.task-item');
        const taskId = taskItem.getAttribute('data-task-id'); // Получаем ID задачи

        // Отправляем запрос на сервер для обновления статуса задачи
        fetch(`/update-task/${taskId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Получаем CSRF-токен
            },
            body: JSON.stringify({complete: event.target.checked}) // Отправляем статус задачи
        })
            .then(handleResponse)
            .then(data => {
                if (data.success) {
                    if (event.target.checked) {
                        moveToCompletedList(taskItem, taskId);
                    } else {
                        moveToTaskList(taskItem, taskId);
                    }
                    updateIncompleteCount(); // Обновляем счетчик невыполненных задач
                } else {
                    alert('Ошибка обновления задачи: ' + data.error);
                }
            })
            .catch(handleError);
    }
}

function moveToCompletedList(taskItem, taskId) {
    const completedItem = createCompletedElement(taskId, taskItem);
    completedList.appendChild(completedItem);
    taskItem.remove(); // Удаляем задачу из списка невыполненных
}

function moveToTaskList(taskItem, taskId) {
    const newTaskItem = createTaskElement(taskId, taskItem.querySelector('label').textContent, taskItem.querySelector('.task-details span').textContent);
    taskList.appendChild(newTaskItem);
    taskItem.remove(); // Удаляем задачу из списка выполненных
}

function createCompletedElement(taskId, taskItem) {
    const completedItem = document.createElement('li');
    completedItem.className = 'completed-item';
    completedItem.setAttribute('data-task-id', taskId);
    completedItem.innerHTML = `
        <label class="completed-label">${taskItem.querySelector('label').textContent}</label>
        <button class="delete-task" aria-label="Удалить задачу">🗑️</button>
    `;
    return completedItem;
}

function handleDeleteTask(event) {
    if (event.target.classList.contains('delete-task')) {
        const taskItem = event.target.closest('[data-task-id]');
        const taskId = taskItem.getAttribute('data-task-id'); // Получаем ID задачи

        // Отправляем запрос на сервер для удаления задачи
        fetch(`/delete-task/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Получаем CSRF-токен
            }
        })
            .then(handleResponse)
            .then(data => {
                if (data.success) {
                    taskItem.remove(); // Удаляем задачу из списка
                    updateIncompleteCount(); // Обновляем счетчик невыполненных задач
                } else {
                    alert('Ошибка удаления задачи: ' + data.error);
                }
            })
            .catch(handleError);
    }
}

// Функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Примените обработчик к задачам, загружаемым из базы данных
document.querySelectorAll('.task-item').forEach(taskItem => {
    const taskId = taskItem.getAttribute('data-task-id'); // Получаем ID из атрибута
    addDeleteTaskHandler(taskItem, taskId); // Передаем ID
});

// Примените обработчик к выполненным задачам
document.querySelectorAll('.completed-item').forEach(completedItem => {
    const taskId = completedItem.getAttribute('data-task-id'); // Получаем ID из атрибута
    addDeleteTaskHandler(completedItem, taskId); // Передаем ID
});

// Функция для добавления обработчика удаления задачи
function addDeleteTaskHandler(taskItem, taskId) {
    const deleteButton = taskItem.querySelector('.delete-task');
    deleteButton.addEventListener('click', function () {
        // Отправляем запрос на сервер для удаления задачи
        fetch(`/delete-task/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Получаем CSRF-токен
            }
        })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                taskItem.remove(); // Удаляем задачу из списка
                updateIncompleteCount(); // Обновляем счетчик невыполненных задач
            } else {
                alert('Ошибка удаления задачи: ' + data.error);
            }
        })
        .catch(handleError);
    });
}

