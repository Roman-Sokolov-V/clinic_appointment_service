FROM ghcr.io/astral-sh/uv:python3.14-alpine3.23

# Працюємо в папці /app
WORKDIR /app

# Оптимізація uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

#д Кешування та встановлення залежностей
#RUN --mount=type=cache,target=/root/.cache/uv \
#    --mount=type=bind,source=uv.lock,target=uv.lock \
#    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#    uv sync --locked --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --extra bot

# Копіюємо код
# 2. Копіюємо суто твій код бота
#COPY telegram_bot/ ./telegram_bot/
#COPY pyproject.toml /app
#COPY uv.lock /app
COPY . /app

# ця змінна для перемикання режиму вибора бд
ENV IN_DOCKER=True


# Фінальна синхронізація проєкту
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra bot

# Додаємо віртуальне оточення в PATH
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
