FROM python:3.12

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install netcat-traditional -y
RUN apt-get upgrade -y && apt-get install postgresql gcc python3-dev musl-dev -y
RUN pip install --upgrade pip

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./entrypoint.sh .

# Делаем скрипт entrypoint исполняемым
RUN chmod +x /usr/src/app/entrypoint.sh

COPY . .

# Создаем пользователя и группу
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Меняем владельца файлов на нового пользователя
RUN chown -R appuser:appgroup /usr/src/app

# Переключаемся на нового пользователя
USER appuser

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]