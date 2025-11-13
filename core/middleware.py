class EmpresaAtivaMiddleware:
    """
    Armazena na request a empresa ativa do usuário
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        empresa_id = request.session.get("empresa_ativa")

        if request.user.is_authenticated and empresa_id:
            from usuarios.models import Empresa
            try:
                request.empresa_ativa = Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                request.empresa_ativa = None
        else:
            request.empresa_ativa = None

        return self.get_response(request)
