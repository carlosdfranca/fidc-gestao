from django.conf import settings
from django.shortcuts import render

import markdown
import os

def home(request):
    # Caminho do release_notes.md
    release_path = os.path.join(settings.BASE_DIR, "static", "docs", "release_notes.md")

    release_html = ""
    if os.path.exists(release_path):
        with open(release_path, "r", encoding="utf-8") as f:
            text = f.read()
            release_html = markdown.markdown(text)

    return render(request, "home.html", {
        "release_notes": release_html
    })

def limites(request):
    return render(request, "limites.html")

def lastro(request):
    return render(request, "lastro.html")

def risco(request):
    return render(request, "risco.html")

def relatorios(request):
    return render(request, "relatorios.html")

def conformidade(request):
    return render(request, "conformidade.html")

def integracoes(request):
    return render(request, "integracoes.html")

def workflow_cessao(request):
    return render(request, "workflow_cessao.html")