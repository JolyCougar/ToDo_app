const dateDisplay = document.getElementById('dateDisplay');
const incompleteCount = document.getElementById('incompleteCount');
const taskList = document.getElementById('taskList');
const completedList = document.getElementById('completedList');
const cookieBanner = document.getElementById('cookieBanner');
const acceptCookiesButton = document.getElementById('acceptCookies');
const addTaskButton = document.getElementById('addTaskButton');
const taskInput = document.getElementById('taskInput');
const taskDescription = document.getElementById('taskDescription');
const modal = document.getElementById('modal');
const closeModal = document.getElementById('closeModal');
const confirmAddTask = document.getElementById('confirmAddTask');

// Настройки
const settingsButton = document.querySelector('.settings');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsModal = document.getElementById('closeSettingsModal');
const settingsForm = document.getElementById('settingsForm');
const fontSelect = document.getElementById('fontSelect');
const fontSizeSelect = document.getElementById('fontSizeSelect');
const showCompletedTasksCheckbox = document.getElementById('showCompletedTasks');
const profileModal = document.getElementById('profileModal');
const editProfileBtn = document.getElementById('editProfileButton');
const closeProfileModalBtn = document.querySelector('#profileModal .close');
const changePasswordButton = document.getElementById('changePasswordButton');
const changePasswordModal = document.getElementById('changePasswordModal');
const closeChangePasswordModal = document.getElementById('closeChangePasswordModal');

if (editProfileBtn) {
    editProfileBtn.onclick = function () {
        profileModal.style.display = 'flex';
    }
}

if (closeProfileModalBtn) {
    closeProfileModalBtn.onclick = function () {
        profileModal.style.display = 'none';
    }
}

// Открытие модального окна смены пароля
if (changePasswordButton) {
    changePasswordButton.onclick = function () {
        changePasswordModal.style.display = 'flex';
    }
}

if (closeChangePasswordModal) {
    closeChangePasswordModal.onclick = function () {
        changePasswordModal.style.display = 'none';
    }
}

// Закрытие модального окна при клике вне его
window.onclick = function (event) {
    if (event.target === profileModal) {
        profileModal.style.display = 'none';
    }
    if (event.target === changePasswordModal) {
        changePasswordModal.style.display = 'none';
    }
}

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
addTaskButton.addEventListener('click', showModal);
closeModal.addEventListener('click', hideModal);
window.addEventListener('click', hideModalOnClickOutside);
document.getElementById('taskForm').addEventListener('submit', addTask);
taskList.addEventListener('change', handleTaskChange);
taskList.addEventListener('click', handleDeleteTask);
completedList.addEventListener('click', handleDeleteTask);

// Обработчики для настроек
settingsButton.addEventListener('click', showSettingsModal);
closeSettingsModal.addEventListener('click', hideSettingsModal);
settingsForm.addEventListener('submit', saveSettings);

// Функции
// Проверка согласия на использование cookies
if (cookieBanner) {
    const acceptCookiesButton = document.getElementById('acceptCookiesButton');
    if (acceptCookiesButton) {
        acceptCookiesButton.addEventListener('click', function () {
            fetch("/accept-cookies/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({accept_cookies: true})
            })
                .then(response => {
                    if (response.ok) {
                        cookieBanner.style.display = 'none';  // Скрываем баннер
                    } else {
                        console.error('Ошибка при обновлении согласия на использование cookies');
                    }
                })
                .catch(error => {
                    console.error('Ошибка:', error);
                });
        });
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

function showSettingsModal() {
    settingsModal.style.display = 'flex';
}

function hideSettingsModal() {
    settingsModal.style.display = 'none';
}

function addTask(event) {
    event.preventDefault();
    const taskName = taskInput.value.trim();
    const taskDescriptionText = taskDescription.value.trim();

    if (!taskName) {
        alert('Пожалуйста, заполните название задачи.');
        return;
    }

    // Показать индикатор загрузки
    const loadingIndicator = document.createElement('div');
    loadingIndicator.textContent = 'Загрузка...';
    document.body.appendChild(loadingIndicator);

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
            // Удалить индикатор загрузки
            loadingIndicator.remove();

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
        .catch(error => {
            loadingIndicator.remove();
            handleError(error);
        });
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
        const taskId = taskItem.getAttribute('data-task-id');

        // Отправляем запрос на сервер для обновления статуса задачи
        fetch(`/update-task/${taskId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({complete: event.target.checked})
        })
            .then(handleResponse)
            .then(data => {
                if (data.success) {
                    if (event.target.checked) {
                        moveToCompletedList(taskItem, taskId);
                    } else {
                        moveToTaskList(taskItem, taskId);
                    }
                    updateIncompleteCount();
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
    taskItem.remove();
}

function moveToTaskList(taskItem, taskId) {
    const newTaskItem = createTaskElement(taskId, taskItem.querySelector('label').textContent, taskItem.querySelector('.task-details span').textContent);
    taskList.appendChild(newTaskItem);
    taskItem.remove();
}

function createCompletedElement(taskId, taskItem) {
    const completedItem = document.createElement('li');
    completedItem.className = 'completed-item';
    completedItem.setAttribute('data-task-id', taskId);
    completedItem.innerHTML = `
        <label class="completed-label">${taskItem.querySelector('label').textContent}</label>
        <span class="completed-label">${taskItem.querySelector('.task-details span').textContent}</span>
        <button class="delete-task" aria-label="Удалить задачу">🗑️</button>
    `;
    return completedItem;
}

function handleDeleteTask(event) {
    if (event.target.classList.contains('delete-task')) {
        const taskItem = event.target.closest('[data-task-id]');
        const taskId = taskItem.getAttribute('data-task-id');

        // Отправляем запрос на сервер для удаления задачи
        fetch(`/delete-task/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(handleResponse)
            .then(data => {
                if (data.success) {
                    taskItem.remove();
                    updateIncompleteCount();
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
    const taskId = taskItem.getAttribute('data-task-id');
    addDeleteTaskHandler(taskItem, taskId);
});

// Примените обработчик к выполненным задачам
document.querySelectorAll('.completed-item').forEach(completedItem => {
    const taskId = completedItem.getAttribute('data-task-id');
    addDeleteTaskHandler(completedItem, taskId);
});

// Функция для добавления обработчика удаления задачи
function addDeleteTaskHandler(taskItem, taskId) {
    const deleteButton = taskItem.querySelector('.delete-task');
    deleteButton.addEventListener('click', function () {
        fetch(`/delete-task/${taskId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
            .then(handleResponse)
            .then(data => {
                if (data.success) {
                    taskItem.remove();
                    updateIncompleteCount();
                } else {
                    alert('Ошибка удаления задачи: ' + data.error);
                }
            })
            .catch(handleError);
    });
}

// Функция для сохранения настроек
function saveSettings(event) {
    event.preventDefault();
    const selectedFont = fontSelect.value;
    const selectedFontSize = fontSizeSelect.value;
    const showCompletedTasks = showCompletedTasksCheckbox.checked;
    const selectedBackground = backgroundSelect.value;

    // Сохранение в localStorage
    localStorage.setItem('font', selectedFont);
    localStorage.setItem('fontSize', selectedFontSize);
    localStorage.setItem('showCompletedTasks', showCompletedTasks);
    localStorage.setItem('background', selectedBackground);
    localStorage.setItem('backgroundColor', selectedBackground);

    if (selectedBackground === 'custom') {
        const customBackground = customBackgroundInput.files[0];
        if (customBackground) {
            const reader = new FileReader();
            reader.onload = function (e) {
                localStorage.setItem('customBackground', e.target.result); // Сохраняем URL пользовательского фона
            }
            reader.readAsDataURL(customBackground);
        }
    } else {
        localStorage.removeItem('customBackground');
        localStorage.setItem('backgroundColor', selectedBackground);// Удаляем пользовательский фон, если выбран предустановленный
    }


    // Применение настроек
    applySettings();

    // Закрытие модального окна настроек
    hideSettingsModal();
}

// Обработчик для чекбокса "Отображать выполненные задачи"
showCompletedTasksCheckbox.addEventListener('change', toggleCompletedTasksVisibility);

backgroundSelect.addEventListener('change', function () {
    if (backgroundSelect.value === 'custom') {
        customBackgroundGroup.style.display = 'block';
    } else {
        customBackgroundGroup.style.display = 'none';
        document.body.className = backgroundSelect.value; // Устанавливаем класс для body
        if (backgroundSelect.value === 'default') {
            document.body.style.backgroundImage = ''; // Убираем фон
        }
    }
});


// Обработчик загрузки пользовательского фона
customBackgroundInput.addEventListener('change', function (event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            document.body.style.backgroundImage = `url(${e.target.result})`;
            document.body.className = 'custom'; // Устанавливаем класс для body
            localStorage.setItem('customBackground', e.target.result); // Сохраняем URL пользовательского фона
        }
        reader.readAsDataURL(file);
    }
});


function toggleCompletedTasksVisibility() {
    const completedSection = document.querySelector('section:nth-of-type(2)'); // Получаем секцию с выполненными задачами
    if (showCompletedTasksCheckbox.checked) {
        completedSection.style.display = 'block'; // Показываем секцию выполненных задач
    } else {
        completedSection.style.display = 'none'; // Скрываем секцию выполненных задач
    }
}

// Примените настройки при загрузке страницы
window.onload = function () {
    applySettings(); // Применяем настройки при загрузке
    toggleCompletedTasksVisibility(); // Применяем видимость выполненных задач при загрузке
};

// Функция для применения настроек
function applySettings() {
    const font = localStorage.getItem('font');
    const fontSize = localStorage.getItem('fontSize');
    const showCompletedTasks = localStorage.getItem('showCompletedTasks') === 'true';
    const background = localStorage.getItem('background') || 'default'; // Получаем фон из localStorage

    if (font) {
        document.body.style.fontFamily = font;
        fontSelect.value = font; // Устанавливаем выбранный шрифт в селекторе
    }
    if (fontSize) {
        document.body.style.fontSize = fontSize + 'px';
        fontSizeSelect.value = fontSize; // Устанавливаем выбранный размер шрифта в селекторе
    }
    showCompletedTasksCheckbox.checked = showCompletedTasks;

    if (background === 'custom') {
        // Если выбран пользовательский фон, не устанавливаем класс
        const customBackground = localStorage.getItem('customBackground');
        if (customBackground) {
            document.body.style.backgroundImage = `url(${customBackground})`;
            document.body.style.backgroundSize = 'cover';
        }
    } else {
        document.body.className = background; // Устанавливаем класс для body
    }

    // Применяем видимость выполненных задач
    toggleCompletedTasksVisibility();
}

function previewAvatar(event) {
    const file = event.target.files[0]; // Получаем файл из input
    const reader = new FileReader(); // Создаем новый объект FileReader

    reader.onload = function (e) {
        const avatarPreview = document.getElementById('avatarPreview'); // Находим элемент для превью
        avatarPreview.src = e.target.result; // Устанавливаем новое изображение
    }

    if (file) {
        reader.readAsDataURL(file); // Читаем файл как Data URL
    } else {
        // Если файл не выбран, устанавливаем изображение по умолчанию
        const defaultAvatar = "{% static 'images/default-avatar.png' %}";
        document.getElementById('avatarPreview').src = defaultAvatar;
    }
}


// Применение настроек при загрузке страницы
window.onload = function () {
    applySettings(); // Применяем настройки при загрузке
    toggleCompletedTasksVisibility(); // Применяем видимость выполненных задач при загрузке
};
