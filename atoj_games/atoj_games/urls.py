"""atoj_games URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from atoj_games import views
from django.conf.urls import include
from django.conf import settings
from django.conf.urls.static import static
import social_django

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.home, name='home'),
    url(r'^register/$', views.user_register, name='user_register'),
    url(r'^login/$', views.user_login, name='user_login'),
    url(r'^logout/$', views.user_logout, name='user_logout'),
    url(r'^user/activate/([0-9a-f]+)/$', views.user_activate, name='user_activate'),
    url('', include('social_django.urls', namespace='social')),
    url(r'^payment/([0-9]+)/$', views.payment_process, name='payment_process'),
    url(r'^payment/result/$', views.payment_result, name='payment_result'),
    url(r'^play/([0-9]+)/$', views.play_game, name='play_game'),
    url(r'^game_load_request/$', views.game_load_request, name='game_load_request'),
    url(r'^game_save_request/$', views.game_save_request, name='game_save_request'),
    url(r'^user_profile/$', views.user_profile, name='user_profile'),
    url(r'^add_highscore/$', views.add_highscore, name='add_highscore'),
    url(r'^browse_games/$', views.browse_games, name='browse_games'),
    url(r'^game/([0-9]+)/$', views.game_profile, name="game_profile"),
    url(r'^uploaded_games/$', views.uploaded_games, name='uploaded_games'),
    url(r'^gamesales/$', views.gamesales, name='gamesales'),
    url(r'^api/get_games_sales/$', views.api_get_games_sales, name='api_get_games_sales'),
    url(r'^api/get_games/$', views.api_get_games, name='api_get_games')

]

# Allows images to be viewed by url
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
