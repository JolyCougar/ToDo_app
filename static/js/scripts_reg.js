 // Открытие и закрытие модального окна
    const licenseModal = document.getElementById("licenseModal");
    const openModalButton = document.getElementById("openModal");
    const closeModalButton = document.getElementsByClassName("close")[0];
    const acceptLicenseButton = document.getElementById("acceptLicense");

    openModalButton.onclick = function (event) {
        event.preventDefault(); // Предотвращаем переход по ссылке
        licenseModal.style.display = "block";
    }

    closeModalButton.onclick = function () {
        licenseModal.style.display = "none";
    }

    acceptLicenseButton.onclick = function () {
        licenseModal.style.display = "none";
    }

    window.onclick = function (event) {
        if (event.target === licenseModal) {
            licenseModal.style.display = "none";
        }
    }

    // Проверка существования пользователя и других условий
    document.getElementById("registrationForm").onsubmit = function (event) {
        event.preventDefault(); // Предотвращаем отправку формы для проверки

        const usernameInput = document.getElementById("id_username").value;
        const passwordInput = document.getElementById("id_password").value;
        const confirmPasswordInput = document.getElementById("id_confirm_password").value;
        const emailInput = document.getElementById("id_email").value;
        const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d!@#$%^&*()_+]{8,}$/; // Обновлено для включения специальных символов
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const errorMessageElement = document.getElementById("error-message");
        const usernameErrorElement = document.getElementById("username-error");
        const emailErrorElement = document.getElementById("email-error");

        // Сброс сообщений об ошибках
        errorMessageElement.style.display = "none";
        usernameErrorElement.style.display = "none";
        emailErrorElement.style.display = "none";

        // Проверка существования имени пользователя
        fetch(`/check-username/?username=${encodeURIComponent(usernameInput)}`)
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    usernameErrorElement.textContent = "Пользователь с таким именем уже существует.";
                    usernameErrorElement.style.display = "block";
                    return; // Прерываем выполнение
                }

                // Проверка существования email
                fetch(`/check-email/?email=${encodeURIComponent(emailInput)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            emailErrorElement.textContent = "Пользователь с таким email уже существует.";
                            emailErrorElement.style.display = "block";
                            return; // Прерываем выполнение
                        }

                        // Проверка сложности пароля
                        if (!passwordPattern.test(passwordInput)) {
                            errorMessageElement.textContent = "Пароль должен содержать минимум 8 символов, включая заглавные буквы, цифры и специальные символы.";
                            errorMessageElement.style.display = "block";
                            return; // Отменяем отправку формы
                        }

                        // Проверка совпадения пароля и подтверждения пароля
                        if (passwordInput !== confirmPasswordInput) {
                            errorMessageElement.textContent = "Пароли не совпадают.";
                            errorMessageElement.style.display = "block";
                            return; // Отменяем отправку формы
                        }

                        // Проверка корректности e-mail
                        if (!emailPattern.test(emailInput)) {
                            errorMessageElement.textContent = "Введите корректный e-mail адрес.";
                            errorMessageElement.style.display = "block";
                            return; // Отменяем отправку формы
                        }

                        // Проверка нажатия чекбокса согласия на лицензионное соглашение
                        const licenseCheckbox = document.getElementById("licenseAgreement");
                        if (!licenseCheckbox.checked) {
                            errorMessageElement.textContent = "Вы должны согласиться с лицензионным соглашением.";
                            errorMessageElement.style.display = "block";
                            return; // Отменяем отправку формы
                        }

                        // Если все проверки пройдены, отправляем форму
                        this.submit();
                    })
                    .catch(error => {
                        console.error('Ошибка при проверке email:', error);
                        errorMessageElement.textContent = "Произошла ошибка при проверке email. Пожалуйста, попробуйте позже";
                        errorMessageElement.style.display = "block";
                    });
            })
            .catch(error => {
                console.error('Ошибка при проверке имени пользователя:', error);
                errorMessageElement.textContent = "Произошла ошибка при проверке имени пользователя. Пожалуйста, попробуйте позже.";
                errorMessageElement.style.display = "block";
            });
    }

    // Функция для показа/скрытия пароля
    const togglePassword = document.getElementById("togglePassword");
    const passwordField = document.getElementById("id_password");
    const confirmPasswordField = document.getElementById("id_confirm_password");

    togglePassword.onclick = function () {
        const type = passwordField.getAttribute("type") === "password" ? "text" : "password";
        passwordField.setAttribute("type", type);
        confirmPasswordField.setAttribute("type", type); // Меняем тип и для поля подтверждения
        this.textContent = type === "password" ? "Показать пароль" : "Скрыть пароль"; // Меняем текст
    }
