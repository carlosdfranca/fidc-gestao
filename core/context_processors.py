from usuarios.models import Empresa, UserEmpresa

def empresas_context(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.is_superuser:
        return {
            "empresas_todas": Empresa.objects.all()
        }
    else:
        return {
            "empresas_todas": Empresa.objects.filter(userempresa__user=request.user)
        }
    

def empresas_disponiveis(request):
    if not request.user.is_authenticated:
        return {}

    # SUPERUSER → Todas as empresas
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = Empresa.objects.filter(userempresa__user=request.user)

    return {
        "empresas_disponiveis": empresas,
        "empresas_qtd": empresas.count(),
    }
