from django.shortcuts import render,redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.utils.datastructures import MultiValueDictKeyError
from django.db.models import Count

from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from django.http import JsonResponse
import inspect
import json

from .form import CustomRegistrationForm
from .form import CustomLoginForm, GameRegisterForm, GameEditForm, RefreshApiKeyForm
from hashlib import md5

from .menu import getTopMenu
from .menu import getPlayerProfileItems

from .models import CustomUser, Setting, Game, PendingPayment, Payment, SaveGame, Player, Developer
from .models import Highscore

def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == "google-oauth2":
        if not user:
            if not hasattr(user, 'customuser'):
              player = Player(user=user)
              player.save()

@login_required(login_url='/login/')
def home(request):
    context = dict()
    context["menu"] = getTopMenu('home')

    games = Game.objects.all()  # get three games for display in home page
    max_games = games.count()

    if max_games > 0:
        games = games[:(3 if max_games > 2 else max_games)]
        context["games"] = games

    # generate dropdown menu items and show currently logged in user, needed for every page with top menu.
    context["current_user"] = request.user
    context["profile_menu_items"] = getPlayerProfileItems()

    if not hasattr(context["current_user"], 'customuser'):
        player = Player(user=context["current_user"])
        player.save()

    return render(request, 'home/home.html', context)

def user_register(request):
    context = dict()

    context['page'] = { 'title': 'Register' }

    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)

        if form.is_valid():
            form.save(request)
            return redirect('user_login')
        else:
            context['form'] = form

    else:
        context['form'] = CustomRegistrationForm()

    return render(request, 'user/register.html', context)

def user_login(request):
    context = dict()

    username = password = ''

    context['page'] = { 'title' : 'Login' }
    context['form'] = CustomLoginForm(request.POST)

    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['member_id'] = user.id
                return redirect('home')

        context['login_error'] = "Authentication failed (maybe account is not yet activated)"

    return render(request, 'user/login.html', context)

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_activate(request, activation_key):

    user = get_object_or_404(CustomUser, activation_key=activation_key)
    user.user.is_active = True
    user.user.save()

    context = dict()
    context['username'] = user.user.username

    return render(request, 'user/activate.html', context)

@login_required(login_url='/login/')
def payment_process(request, game_id):
    current_user = request.user
    current_customuser = CustomUser.objects.get(user=current_user)

    game = get_object_or_404(Game, id=game_id)
    amount = game.price

    # Check if game already owned or buyer is developer of
    try:
        dev = Developer.objects.get(user=current_user)
    except Developer.DoesNotExist:
        dev = None

    if current_customuser in game.bought_by_user.all() or dev == game.developer:
        game_already_owned = True
    else:
        game_already_owned = False

    # Check if user has another payment pending
    pending_payment = PendingPayment.objects.filter(buyer=current_customuser)
    if pending_payment:
        # Previous payment pending, delete it
        pending_payment.delete()

    # Create new pending payment
    pending_payment = PendingPayment.objects.create(buyer=current_customuser,
                        amount=amount, game=game)
    payment_id = pending_payment.id

    # Calculate checksum using secret key
    seller_id = Setting.objects.get(name='seller_id').value
    secret_key = Setting.objects.get(name='secret_key').value
    checksumstr = 'pid={}&sid={}&amount={}&token={}'.format(
                    payment_id, seller_id, amount, secret_key)
    m = md5(checksumstr.encode('ascii'))
    checksum = m.hexdigest()

    context = dict()
    context['game_already_owned'] = game_already_owned
    context['current_user'] = current_user
    context['game'] = game
    context['checksum'] = checksum
    context['pid'] = payment_id
    context['sid'] = seller_id
    context['amount'] = amount
    context['next_url'] = 'http://' + request.META['HTTP_HOST'] +'/payment/result'
    context['home_page'] = 'http://' + request.META['HTTP_HOST']
    context['profile_menu_items'] = getPlayerProfileItems()

    return render(request, 'payment/details.html', context)

@login_required(login_url='/login/')
def payment_result(request):
    context = dict()
    current_user = request.user
    secret_key = Setting.objects.get(name='secret_key').value

    # received GET values
    payment_id = request.GET.get('pid')
    ref = request.GET.get('ref')
    result = request.GET.get('result')
    checksum = request.GET.get('checksum') # received checksum

    # Game
    game = PendingPayment.objects.get(id=payment_id).game

    # Check pending payment and result value. Determine message and next_destination
    # If result is error or cancel PendingPayment is deleted and return is called
    pending_payment_queryset = PendingPayment.objects.filter(id=payment_id)
    if not pending_payment_queryset:
        context['message'] = 'Requested payment does not exist!'
        context['next_destination'] = '/' # Home
        return render(request, 'payment/result.html', context)

    elif result == 'cancel':
        context['message'] = 'Payment was canceled by the user.'
        context['next_destination'] = '/' # Home
        # Cancel payment
        pending_payment_queryset.delete()
        return render(request, 'payment/result.html', context)

    elif result == 'error':
        context['message'] = 'Payment was canceled by the payment service.'
        context['next_destination'] = '/' # Home
        # Cancel payment
        pending_payment_queryset.delete()
        return render(request, 'payment/result.html', context)


    # Calculate checksum from received values and compare
    checksum_string = "pid={}&ref={}&result={}&token={}".format(
                            payment_id, ref, result, secret_key)
    m = md5(checksum_string.encode("ascii"))
    checksum_generated = m.hexdigest()

    if checksum == checksum_generated:
        context['next_destination'] = '/game/' + str(game.id) # Game's page
        context['message'] = 'Payment was succesful!'

    else:
        context['message'] = 'Payment was canceled due to failed authentication.'
        context['next_destination'] = '/' # Home

    # Create payment and delete pending payment
    pending_payment = PendingPayment.objects.get(id=payment_id)
    payment = Payment.objects.create(bought_game=pending_payment.game,
                buyer=pending_payment.buyer, amount=pending_payment.amount,
                payment_app_ref=ref)
    pending_payment.delete()

    # Add buyer as bought user in game
    current_customuser = CustomUser.objects.get(user=current_user)
    game.bought_by_user.add(current_customuser)

    context['game'] = game
    context['current_user'] = current_user
    context['profile_menu_items'] = getPlayerProfileItems()
    return render(request, 'payment/result.html', context)

@login_required(login_url='/login/')
def play_game(request, game_id):
    context = dict()

    # Get game info
    game = get_object_or_404(Game, id=game_id)
    context["profile_menu_items"] = getPlayerProfileItems()
    context["current_user"] = request.user
    context['game_url'] = game.url
    context['game_name'] = game.name
    context['game_id'] = game_id

    return render(request, 'game/play.html', context)

@login_required(login_url='/login/')
def game_load_request(request):
    current_user = request.user
    current_customuser = None

    print(CustomUser.objects.all())

    if not inspect.isclass(current_user):
        current_customuser = CustomUser.objects.get(user__username=current_user)
    else:
        current_customuser = CustomUser.objects.get(user=current_user)

    current_customuser = current_user.customuser
    game_id = request.GET['gameID']

    # Get game or 404
    game = get_object_or_404(Game, id=game_id)

    # Get save or 404
    save = get_object_or_404(SaveGame, user=current_customuser, game=game)

    game_state = save.data
    return JsonResponse(game_state, safe=False)

@login_required(login_url='/login/')
def game_save_request(request):
    # Saves the data. Existing save is replaced
    current_user = request.user
    current_customuser = CustomUser.objects.get(user=current_user)
    game_id = request.GET['gameId']
    print(game_id)
    game_state = request.GET['gameState']
    print(game_state)

    # Get game or 404
    game = get_object_or_404(Game, id=game_id)

    try:
        old_save = SaveGame.objects.get(user=current_customuser, game=game)
        old_save.data = game_state
        old_save.save()
    except ObjectDoesNotExist:
        SaveGame.objects.create(user=current_customuser, game=game, data=game_state)

    return HttpResponse(request)

@login_required(login_url='/login/')
def add_highscore(request):
    # Saves given score.
    current_user = request.user
    current_customuser = CustomUser.objects.get(user=current_user)
    game_id = request.GET['gameId']
    score = request.GET['score']

    # Get game or 404
    game = get_object_or_404(Game, id=game_id)

    scores = Highscore.objects.filter(game=game)
    ordered_scores = Highscore.objects.order_by('-score') # Descending order
    list_lenght = Highscore.objects.filter(game=game).count()

    # If less than 10 entires, add regardless of score value
    if list_lenght < 10:
        Highscore.objects.create(game=game, user=current_customuser, score=score)

    else:
        # If new score is larger than any of the scores in queryset
        # then replace last
        for i in range(0, list_lenght):
            if ordered_scores[i].score < float(score):
                ordered_scores[list_lenght-1].delete()
                Highscore.objects.create(game=game, user=current_customuser, score=score)
                break


    return HttpResponse(request)

@login_required(login_url='/login/')
def user_profile(request):
    context = dict()
    current_user = request.user
    # decide if the current user is developer, for display differently in user_profile page

    try:
        developer = Developer.objects.all().get(user=current_user)
        context["developer"] = developer
        is_developer = True
    except Developer.DoesNotExist:
        is_developer = False
    # save game to db
    if request.method == 'POST' and 'refresh' in request.POST:
        api_form = RefreshApiKeyForm(request.POST or None)
        if api_form.is_valid:
            api_form.save(developer.user.id)
            developer = Developer.objects.all().get(user=current_user)
            context["developer"] = developer

    if request.method == 'POST' and not 'refresh' in request.POST:
        form = GameRegisterForm(request.POST or None,request.FILES or None)
        if form.is_valid:
            instance = form.save(commit=False)
            instance.developer = Developer.objects.all().get(user=current_user)
            instance.save()
    else:
        form = GameRegisterForm()
    context["current_user"] = current_user
    context["profile_menu_items"] = getPlayerProfileItems()
    context["is_developer"] = is_developer
    context["form"] = form
    return render(request, 'user/user_profile.html', context)

@login_required(login_url='/login/')
def browse_games(request):
    context = dict()
    current_user = request.user

    try:
        dev = Developer.objects.all().get(user=current_user)
        is_developer = True
    except Developer.DoesNotExist:
        dev = None
        is_developer = False

    custom_user = None
    print(current_user)

    if hasattr(current_user, 'customuser'):
        custom_user = current_user.customuser
    else:
        redirect('home')

    context['games'] = Game.objects.all()
    context["profile_menu_items"] = getPlayerProfileItems()
    context["current_user"] = current_user
    # search based on games' name.
    query = request.GET.get('query')
    if query:
        game_searched = Game.objects.all().filter(name__contains=query)
        context["games"] = game_searched

    # Check if game is bought by the user or is developer of
    current_customuser = CustomUser.objects.get(user=current_user)
    for game in context['games']:
        if current_customuser in game.bought_by_user.all() or dev == game.developer:
            game.has_bought = True
        else:
            game.has_bought = False

    return render(request, 'game/browse.html', context)

@login_required(login_url='/login/')
def game_profile(request, game_id):
    context = dict()
    current_user = request.user
    context["profile_menu_items"] = getPlayerProfileItems()
    context["current_user"] = current_user
    if hasattr(current_user, 'customuser'):
        custom_user = current_user.customuser
    else:
        redirect('browse_games')

    try:
        context['game'] = Game.objects.get(id=int(game_id))
    except Game.DoesNotExist:
        raise Http404()

    # Check if game is bought by the user or developed by the user
    try:
        dev = Developer.objects.all().get(user=current_user)
    except Developer.DoesNotExist:
        dev = None

    current_customuser = CustomUser.objects.get(user=current_user)
    if (current_customuser in context['game'].bought_by_user.all()
            or dev == context['game'].developer):
        context['can_play'] = True
    else:
        context['can_play'] = False

    print(context['game'])

    return render(request, 'game/profile.html', context)

@login_required(login_url='/login/')
def uploaded_games(request):
    context = dict()
    context['error_message'] = ''
    context['error'] = False
    current_user = request.user
    game_id = None

    # Test if user is developer and get games for the developer
    try:
        Developer.objects.all().get(user=current_user)
        is_developer = True
    except Developer.DoesNotExist:
        is_developer = False
        context['error_message'] = 'You have not signed in as a developer.'
        context['error'] = True

    if is_developer:
        dev = Developer.objects.all().get(user=current_user)
        game_all = Game.objects.filter(developer=dev)
    else:
        dev = None
        game_all = None
        context['error_message'] = 'You do not have any uploaded games.'
        context['error'] = True



    # If POST edit the selected game with form's values
    if request.method == 'POST':
        game_id = request.POST['game_id']
        game = get_object_or_404(Game, id=game_id,  developer=dev)
        form = GameEditForm(request.POST or None,request.FILES or None, instance=game)
        if form.is_valid:
            instance = form.save(commit=False)
            instance.developer = Developer.objects.all().get(user=current_user)
            instance.save()
    # Else fetch selected game's info so it can be shown to the dev
    else:
        try:
            game_id = request.GET['selected_game']
            game = get_object_or_404(Game, id=game_id, developer=dev)
            form = GameEditForm(instance=game)
        except MultiValueDictKeyError:
            form = None

    context['is_developer'] = is_developer
    context['form'] = form
    context['current_user'] = current_user
    context['profile_menu_items'] = getPlayerProfileItems()
    context['game_list'] = game_all
    context['selected_game'] = game_id
    return render(request, 'user/uploaded_games.html', context)


@login_required(login_url='/login/')
def gamesales(request):
    context = dict()
    context['error_message'] = ''
    context['error'] = False
    current_user = request.user
    game_id = None

    # Test if user is developer and get games for the developer
    try:
        Developer.objects.all().get(user=current_user)
        is_developer = True
    except Developer.DoesNotExist:
        is_developer = False
        context['error_message'] = 'You have not signed in as a developer.'
        context['error'] = True

    if is_developer:
        dev = Developer.objects.all().get(user=current_user)
        game_all = Game.objects.filter(developer=dev)
    else:
        dev = None
        game_all = None
        context['error_message'] = 'You do not have any uploaded games.'
        context['error'] = True

    sold = None
    sold_g = []
    sales = []
    if is_developer:
        dev = Developer.objects.all().get(user=current_user)
        sold = list(Game.objects.annotate(amount_sold=Count('bought_by_user')).filter(developer=dev).values('name', 'price', 'amount_sold'))
        for game in game_all:
            sold_g.append(list(Game.objects.annotate(amount_sold=Count('bought_by_user')).filter(id = game.id).values('name', 'price', 'amount_sold')))
            sales.append(list(Payment.objects.filter(bought_game = game.id)))
            #sales.append(list(Payment.objects.filter(bought_game = game.id).values('bought_game', 'buyer', 'amount', 'completion_date')))
    try:
        game_id = request.GET['selected_game']
        game = get_object_or_404(Game, id=game_id, developer=dev)
        form = GameEditForm(instance=game)
    except MultiValueDictKeyError:
        form = None

    context['is_developer'] = is_developer
    context['form'] = form
    context['current_user'] = current_user
    context['profile_menu_items'] = getPlayerProfileItems()
    context['game_list'] = game_all
    context['selected_game'] = game_id
    context['sold'] = sold
    context['sales'] = sales
    return render(request, 'user/gamesales.html', context)

def api_get_games_sales(request):
    if request.method == 'GET':

        if request.GET.get('api-key'):
            try:
                developer = Developer.objects.get(api_key=request.GET.get('api-key'))
            except Developer.DoesNotExist:
                return HttpResponse("Developer not found", status=404)

            json_resp = dict()
            json_resp['games'] = list(Game.objects.annotate(amount_sold=Count('bought_by_user')).filter(developer=developer).values('name', 'price', 'amount_sold'))
            return JsonResponse(json_resp, safe=False)

    return HttpResponse("GET request required", status=404)

def api_get_games(request):
    json_resp = dict()
    json_resp['games'] = list(Game.objects.all().values('name', 'price'))

    for game in json_resp['games']:
        game['high_scores'] = list(Highscore.objects.filter(game__name=game['name']).values('score'))[:10]

    return JsonResponse(json_resp, safe=False)
