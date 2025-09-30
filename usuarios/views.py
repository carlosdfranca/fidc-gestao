from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash, get_user_model
from django.core.cache import cache
from .forms import ProfileForm

import random

@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()

            # Atualiza a sessão caso tenha alterado a senha
            if form.cleaned_data.get("password1"):
                update_session_auth_hash(request, user)

            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("profile")
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "usuarios/profile.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            # Gerar código OTP
            otp = str(random.randint(100000, 999999))
            cache.set(f"otp_{user.id}", otp, timeout=300)  # expira em 5 min

            # Simula envio do OTP (aqui só printa no terminal)
            print(f"[OTP] Código para {user.username}: {otp}")

            # Armazena ID do user na sessão para validar depois
            request.session["otp_user_id"] = user.id

            return redirect("otp")
        else:
            messages.error(request, "Usuário ou senha inválidos.")
    return render(request, "registration/login.html")

def otp_view(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        user_id = request.session.get("otp_user_id")

        if not user_id:
            messages.error(request, "Sessão expirada. Faça login novamente.")
            return redirect("login")

        user = get_user_model().objects.get(id=user_id)
        otp_real = cache.get(f"otp_{user.id}")

        if otp_input == otp_real:
            login(request, user)
            cache.delete(f"otp_{user.id}")  # limpa OTP
            del request.session["otp_user_id"]
            messages.success(request, "Login realizado com sucesso!")
            return redirect("home")
        else:
            messages.error(request, "Código OTP inválido. Tente novamente.")

    return render(request, "registration/otp.html")