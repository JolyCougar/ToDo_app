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

// Функции
function hideCookieBanner() {
    cookieBanner.style.display = 'none';
}

function toggleCompletedList() {
    const isHidden = completedList.style.display === 'none' || completedList.style.display === '';
    completedList.style.display = isHidden ? 'block' : 'none';
    toggleCompletedListButton.textContent = isHidden ? 'Свернуть' : 'Развернуть';
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
        body: JSON.stringify({ name: taskName, description: taskDescriptionText })
    })
    .then(handleResponse)
    .then(data => {
        if (data.success) {
            addTaskToDOM(data.task_id, taskName, taskDescriptionText, data.create_at); // Передаем время создания
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
    const newTaskItem = document.createElement('li');
    newTaskItem.className = 'task-item';
    newTaskItem.setAttribute('data-task-id', taskId);
    newTaskItem.innerHTML = `
        <input type="checkbox" id="task${taskId}" complete="false">
        <label for="task${taskId}">${taskName}</label>
        <span class="task-details">
            <span>${taskDescriptionText}</span>
        </span>
        <button class="delete-task">🗑️</button>
    `;

    taskList.appendChild(newTaskItem);
    addDeleteTaskHandler(newTaskItem, taskId);
}



// Функция для обновления счетчика невыполненных задач
function updateIncompleteCount() {
    const checkboxes = taskList.querySelectorAll('input[type="checkbox"]');
    const completedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;
    incompleteCount.textContent = checkboxes.length - completedCount; // Обновляем текст счетчика
}

// Обработчик нажатия на чекбоксы
taskList.addEventListener('change', function (event) {
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
            body: JSON.stringify({ complete: event.target.checked }) // Отправляем статус задачи
        })
        .then(handleResponse)
        .then(data => {
            if (data.success) {
                // Обновляем интерфейс в зависимости от статуса
                if (event.target.checked) {
                    // Перемещаем задачу в список выполненных
                    const completedItem = document.createElement('li');
                    completedItem.className = 'completed-item';
                    completedItem.setAttribute('data-task-id', taskId); // Устанавливаем ID задачи
                    completedItem.innerHTML = `
                        <label class="completed-label">${taskItem.querySelector('label').textContent}</label>
                        <button class="delete-task">🗑️</button>
                    `;
                    completedList.appendChild(completedItem);
                    taskItem.remove(); // Удаляем задачу из списка невыполненных
                    addDeleteTaskHandler(completedItem, taskId); // Добавляем обработчик для удаления выполненной задачи
                } else {
                    // Если чекбокс снят, возвращаем задачу обратно
                    const newTaskItem = document.createElement('li');
                    newTaskItem.className = 'task-item';
                    newTaskItem.setAttribute('data-task-id', taskId); // Устанавливаем ID задачи
                    newTaskItem.innerHTML = `
                        <input type="checkbox" id="task${taskId}">
                        <label for="task${taskId}">${taskItem.querySelector('label').textContent}</label>
                        <span class="task-details">
                            <span>${taskItem.querySelector('.task-details span').textContent}</span>
                            <span class="task-date">${taskItem.querySelector('.task-date').textContent}</span>
                        </span>
                        <button class="delete-task">🗑️</button>
                    `;
                    taskList.appendChild(newTaskItem);
                    taskItem.remove(); // Удаляем задачу из списка выполненных
                    addDeleteTaskHandler(newTaskItem, taskId); // Добавляем обработчик для новой задачи
                }
                updateIncompleteCount(); // Обновляем счетчик невыполненных задач
            } else {
                alert('Ошибка обновления задачи: ' + data.error);
            }
        })
        .catch(handleError);
    }
});

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



