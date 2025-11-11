from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser

class ProfileForm(UserChangeForm):
    password = None  # escondemos o campo padrão

    password1 = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Digite a nova senha"}),
        required=False
    )
    password2 = forms.CharField(
        label="Confirmar Nova Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirme a nova senha"}),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "profile_image"]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("As senhas não coincidem.")
            if len(password1) < 6:
                raise forms.ValidationError("A senha deve ter pelo menos 6 caracteres.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get("password1")

        if password1:
            user.set_password(password1)

        if commit:
            user.save()
        return user
