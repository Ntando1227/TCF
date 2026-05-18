from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect

from .forms import CustomUserCreationForm


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')

    else:
        form = CustomUserCreationForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
        }
    )


@login_required
def logout_view(request):
    logout(request)

    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect


@login_required
def account_settings(request):
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()

        if hasattr(user, 'theme_preference'):
            user.theme_preference = request.POST.get('theme_preference', 'dark')

        user.save()

        messages.success(request, 'Account settings updated successfully.')

        return redirect('account_settings')

    return render(request, 'accounts/account_settings.html')
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages


@login_required
def account_settings(request):
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()

        user.save()

        messages.success(request, 'Account settings updated successfully.')

        return redirect('account_settings')

    return render(request, 'accounts/account_settings.html')
