from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^index$', views.index, name='index'),
    url(r'^search$', views.search, name='search'),
    url(r'^profile$', views.profile, name='profile'),
    url(r'^bookings$', views.bookings, name='bookings'),
    url(r'^wallet$', views.wallet, name='wallet'),
    url(r'^book$', views.book, name='book'),
    url(r'^confirmation$', views.confirmation, name='confirmation'),
]
