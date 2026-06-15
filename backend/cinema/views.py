import datetime

from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Movie, Ticket, Token, User


# ---------------------------------------------------------------------------
# Вспомогательная функция — достать пользователя из сессии
# ---------------------------------------------------------------------------

def get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Регистрация — GET показывает форму, POST сохраняет пользователя
# ---------------------------------------------------------------------------

def register_view(request):
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        password  = request.POST.get('password', '').strip()
        full_name = request.POST.get('full_name', '').strip()

        if not username or not password or not full_name:
            messages.error(request, 'Все поля обязательны')
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует')
            return render(request, 'register.html')

        user = User(username=username, full_name=full_name)
        user.set_password(password)
        user.save()

        # Сразу логиним после регистрации
        request.session['user_id'] = user.id
        return redirect('movies')

    return render(request, 'register.html')


# ---------------------------------------------------------------------------
# Вход
# ---------------------------------------------------------------------------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Введите логин и пароль')
            return render(request, 'login.html')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Неверный логин или пароль')
            return render(request, 'login.html')

        if not user.verify_password(password):
            messages.error(request, 'Неверный логин или пароль')
            return render(request, 'login.html')

        request.session['user_id'] = user.id
        return redirect('movies')

    return render(request, 'login.html')


# ---------------------------------------------------------------------------
# Выход
# ---------------------------------------------------------------------------

def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---------------------------------------------------------------------------
# Афиша фильмов — с фильтрацией и сортировкой
# ---------------------------------------------------------------------------

def movies_view(request):
    movies = Movie.objects.all()

    genre      = request.GET.get('genre', '')
    age_rating = request.GET.get('age_rating', '')
    sort       = request.GET.get('sort', '')

    if genre:
        movies = movies.filter(genre=genre)
    if age_rating:
        movies = movies.filter(age_rating=age_rating)
    if sort == 'price_asc':
        movies = movies.order_by('ticket_price')
    elif sort == 'price_desc':
        movies = movies.order_by('-ticket_price')

    user = get_current_user(request)

    today = datetime.date.today().isoformat()

    return render(request, 'movies.html', {
        'movies':     movies,
        'user':       user,
        'genre':      genre,
        'age_rating': age_rating,
        'sort':       sort,
        'today':      today,
    })


# ---------------------------------------------------------------------------
# Покупка билета — POST из карточки фильма на movies.html
# ---------------------------------------------------------------------------

def buy_ticket_view(request, movie_id):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        show_date_str = request.POST.get('show_date', '').strip()
        quantity_str  = request.POST.get('quantity', '').strip()

        # Валидация количества
        try:
            quantity = int(quantity_str)
            if quantity < 1:
                raise ValueError
        except ValueError:
            messages.error(request, 'Количество билетов должно быть не менее 1')
            return redirect('movies')

        # Валидация даты
        try:
            show_date = datetime.date.fromisoformat(show_date_str)
        except ValueError:
            messages.error(request, 'Некорректный формат даты')
            return redirect('movies')

        if show_date < datetime.date.today():
            messages.error(request, 'Дата сеанса не может быть в прошлом')
            return redirect('movies')

        try:
            movie = Movie.objects.get(pk=movie_id)
        except Movie.DoesNotExist:
            messages.error(request, 'Фильм не найден')
            return redirect('movies')

        Ticket.objects.create(
            user=user,
            movie=movie,
            show_date=show_date,
            quantity=quantity,
            total_price=movie.ticket_price * quantity,
        )

        messages.success(request, f'Билет на «{movie.title}» успешно куплен!')
        return redirect('movies')

    return redirect('movies')


# ---------------------------------------------------------------------------
# Профиль — данные пользователя + список билетов
# ---------------------------------------------------------------------------

def profile_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    tickets = (
        Ticket.objects
        .filter(user=user)
        .select_related('movie')
        .order_by('-created_at')
    )

    return render(request, 'profile.html', {
        'user':    user,
        'tickets': tickets,
    })


# ---------------------------------------------------------------------------
# Возврат билета
# ---------------------------------------------------------------------------

def refund_ticket_view(request, ticket_id):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        try:
            ticket = Ticket.objects.get(pk=ticket_id, user=user)
        except Ticket.DoesNotExist:
            messages.error(request, 'Билет не найден')
            return redirect('profile')

        if ticket.status == Ticket.STATUS_REFUNDED:
            messages.error(request, 'Билет уже возвращён')
        else:
            ticket.status = Ticket.STATUS_REFUNDED
            ticket.save()
            messages.success(request, 'Возврат билета оформлен')

    return redirect('profile')


# ---------------------------------------------------------------------------
# Загрузка аватара
# ---------------------------------------------------------------------------

def avatar_upload_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if request.method == 'POST':
        avatar = request.FILES.get('avatar')

        if not avatar:
            messages.error(request, 'Выберите файл')
            return redirect('profile')

        if avatar.content_type not in ['image/jpeg', 'image/png']:
            messages.error(request, 'Допустимые форматы: JPG, PNG')
            return redirect('profile')

        user.avatar = avatar
        user.save()
        messages.success(request, 'Фото профиля обновлено')

    return redirect('profile')