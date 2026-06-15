import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.db import models


class User(models.Model):
    """
    Пользователь. Пароль хранится хэшированным через make_password/check_password.
    Никакого AbstractUser — чистый models.Model.
    """
    username = models.CharField('Логин', max_length=150, unique=True)
    password_hash = models.CharField('Хэш пароля', max_length=255)
    full_name = models.CharField('Полное имя', max_length=255)
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',   # сохраняется в media/avatars/
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def set_password(self, raw_password):
        """Хэшируем пароль перед сохранением."""
        self.password_hash = make_password(raw_password)

    def verify_password(self, raw_password):
        """Проверяем пароль при логине."""
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return self.username


class Token(models.Model):
    """
    Токен авторизации — UUID-строка, привязанная к пользователю.
    Хранится на клиенте в localStorage, передаётся в заголовке Authorization: Token <key>.
    """
    key = models.CharField(
        'Токен',
        max_length=64,
        unique=True,
        default=uuid.uuid4,  # генерируется автоматически при создании
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='token',
        verbose_name='Пользователь',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'tokens'
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'

    def __str__(self):
        return f'{self.user.username}: {self.key}'


class Movie(models.Model):
    """
    Фильм в афише.
    genre хранится как целое число: 1=боевик, 2=комедия, 3=драма — как в seed.sql.
    """
    GENRE_ACTION = 1
    GENRE_COMEDY = 2
    GENRE_DRAMA = 3

    GENRE_CHOICES = [
        (GENRE_ACTION, 'Боевик'),
        (GENRE_COMEDY, 'Комедия'),
        (GENRE_DRAMA, 'Драма'),
    ]

    title = models.CharField('Название', max_length=255)
    genre = models.IntegerField('Жанр', choices=GENRE_CHOICES)
    ticket_price = models.PositiveIntegerField('Цена билета (тг)')
    age_rating = models.PositiveSmallIntegerField('Возрастной рейтинг')  # 6, 12, 16, 18
    description = models.TextField('Описание')
    poster_path = models.CharField(
        'Путь к постеру',
        max_length=255,
        # Значение из seed.sql: 'images/posters/movie1.jpg'
        # Фронтенд строит полный URL: /static/images/posters/movie1.jpg
    )

    class Meta:
        db_table = 'movies'
        verbose_name = 'Фильм'
        verbose_name_plural = 'Фильмы'

    def __str__(self):
        return self.title


class Ticket(models.Model):
    """
    Купленный билет.
    total_price считается автоматически в API-view: ticket_price * quantity.
    """
    STATUS_ACTIVE = 'active'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Активен'),
        (STATUS_REFUNDED, 'Возвращён'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Пользователь',
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='Фильм',
    )
    show_date = models.DateField('Дата сеанса')
    quantity = models.PositiveIntegerField('Количество билетов')
    total_price = models.PositiveIntegerField('Итоговая стоимость')
    status = models.CharField(
        'Статус',
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    created_at = models.DateTimeField('Дата покупки', auto_now_add=True)

    class Meta:
        db_table = 'tickets'
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

    def __str__(self):
        return f'{self.user.username} — {self.movie.title} ({self.show_date})'