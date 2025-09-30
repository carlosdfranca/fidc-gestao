from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from .forms import ProfileForm

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
