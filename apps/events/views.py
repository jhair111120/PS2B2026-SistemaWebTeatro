from django.shortcuts import render, get_object_or_404
from .models import Evento

def comprar_entrada_view(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    return render(request, 'pages/users/comprar_entrada.html', {'evento': evento})
