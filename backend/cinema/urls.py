from django.urls import path
from . import views

urlpatterns = [
    path('',                                views.movies_view,       name='movies'),
    path('register/',                       views.register_view,     name='register'),
    path('login/',                          views.login_view,        name='login'),
    path('logout/',                         views.logout_view,       name='logout'),
    path('profile/',                        views.profile_view,      name='profile'),
    path('tickets/buy/<int:movie_id>/',     views.buy_ticket_view,   name='buy_ticket'),
    path('tickets/refund/<int:ticket_id>/', views.refund_ticket_view,name='refund_ticket'),
    path('profile/avatar/',                 views.avatar_upload_view,name='avatar_upload'),
]