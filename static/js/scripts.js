const dateDisplay = document.getElementById('dateDisplay');
const incompleteCount = document.getElementById('incompleteCount');
const taskList = document.getElementById('taskList');
const completedList = document.getElementById('completedList');
const cookieBanner = document.getElementById('cookieBanner');
const acceptCookiesButton = document.getElementById('acceptCookies');
const toggleCompletedListButton = document.getElementById('toggleCompletedList');
const addTaskButton = document.getElementById('addTaskButton');
const taskInput = document.getElementById('taskInput');
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

// Обработчик нажатия на кнопку "Принять"
acceptCookiesButton.addEventListener('click', function () {
    cookieBanner.style.display = 'none'; // Скрываем баннер
});

// Обработчик нажатия на кнопку сворачивания/разворачивания
toggleCompletedListButton.addEventListener('click', function () {
    if (completedList.style.display === 'none' || completedList.style.display === '') {
        completedList.style.display = 'block';
        toggleCompletedListButton.textContent = 'Свернуть';
    } else {
        completedList.style.display = 'none';
        toggleCompletedListButton.textContent = 'Развернуть';
    }
});

// Обработчик нажатия на кнопку "Добавить задачу"
addTaskButton.addEventListener('click', function () {
    modal.style.display = 'block'; // Показываем модальное окно
    taskInput.focus(); // Устанавливаем фокус на поле ввода
});

// Обработчик нажатия на кнопку закрытия модального окна
closeModal.addEventListener('click', function () {
    modal.style.display = 'none'; // Скрываем модальное окно
});

// Обработчик нажатия вне модального окна
window.addEventListener('click', function (event) {
    if (event.target === modal) {
        modal.style.display = 'none'; // Скрываем модальное окно
    }
});

// Обработчик нажатия на кнопку "Добавить" в модальном окне
confirmAddTask.addEventListener('click', function () {
    const taskText = taskInput.value;

    if (taskText.trim() === '') {
        alert('Пожалуйста, введите задачу.'); // Проверка на пустое значение
        return;
    }

    // Создаем новый элемент списка
    const newTaskItem = document.createElement('li');
    newTaskItem.className = 'task-item';
    const taskId = Date.now(); // Генерируем уникальный ID для задачи
    newTaskItem.innerHTML = `
        <input type="checkbox" id="task${taskId}">
        <label for="task${taskId}">${taskText}</label>
        <button class="delete-task">🗑️</button>
    `;

    // Добавляем новый элемент в список задач
    taskList.appendChild(newTaskItem);
    console.log('Добавлена новая задача:', taskText); // Для отладки
    taskInput.value = ''; // Очищаем поле ввода
    modal.style.display = 'none'; // Скрываем модальное окно после добавления задачи

    // Обновляем счетчик невыполненных задач
    updateIncompleteCount();

    // Добавляем обработчик для удаления новой задачи
    addDeleteTaskHandler(newTaskItem, taskId);
});

// Функция для обновления счетчика невыполненных задач
function updateIncompleteCount() {
    const checkboxes = taskList.querySelectorAll('input[type="checkbox"]');
    console.log('Количество чекбоксов:', checkboxes.length); // Для отладки
    const completedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;
    incompleteCount.textContent = checkboxes.length - completedCount; // Обновляем текст счетчика
}

// Обработчик нажатия на чекбоксы
taskList.addEventListener('change', function (event) {
    if (event.target.type === 'checkbox') {
        console.log('Чекбокс изменен:', event.target.id); // Для отладки
        const taskItem = event.target.closest('.task-item');
        const taskId = taskItem.querySelector('input[type="checkbox"]').id.replace('task', ''); // Получаем ID задачи

        // Отправляем запрос на сервер для обновления статуса задачи
        fetch(`/update-task/${taskId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Получаем CSRF-токен
            },
            body: JSON.stringify({ complete: event.target.checked }) // Отправляем статус задачи
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем интерфейс в зависимости от статуса
                if (event.target.checked) {
                    // Перемещаем задачу в список выполненных
                    const completedItem = document.createElement('li');
                    completedItem.className = 'completed-item';
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
                    newTaskItem.innerHTML = `
                        <input type="checkbox" id="task${taskId}">
                        <label for="task${taskId}">${taskItem.querySelector('label').textContent}</label>
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
        });
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                taskItem.remove(); // Удаляем задачу из списка
                updateIncompleteCount(); // Обновляем счетчик невыполненных задач
            } else {
                alert('Ошибка удаления задачи: ' + data.error);
            }
        });
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

