from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from rest_framework import generics

from .models import RegistroCotacao
from .serializers import RegistroCotacaoSerializer


def consultar_cotacao(request):
    contexto = {}
    try:
        # timeout evita que a página fique esperando para sempre
        resposta = requests.get(settings.COTACAO_URL, timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()

        # 1) Primeiro valida TODAS as moedas, sem gravar nada.
        #    A API devolve um dicionário: {"USDBRL": {...}, "EURBRL": {...}, ...}
        novos = []
        for item in dados.values():
            novos.append(RegistroCotacao(
                moeda_origem=item['code'],
                moeda_destino=item['codein'],
                valor=Decimal(item['bid']),
            ))
        if not novos:
            raise ValueError('A API não devolveu nenhuma cotação.')

        # 2) Só então grava tudo de uma vez: ou salva todas, ou nenhuma.
        with transaction.atomic():
            for registro in novos:
                registro.save()

        contexto = {'sucesso': True, 'registros': novos}
    except requests.exceptions.RequestException:
        contexto = {'erro': 'Não foi possível consultar a cotação agora. Tente novamente em instantes.'}
    except (ValueError, KeyError, TypeError, AttributeError, InvalidOperation):
        # A API respondeu, mas em um formato inesperado.
        contexto = {'erro': 'A API externa respondeu em um formato inesperado.'}
    return render(request, 'painel/consultar.html', contexto)


class HistoricoCotacaoView(generics.ListAPIView):
    """Somente leitura: histórico do mais recente para o mais antigo.

    Filtro opcional: /api/historico/?moeda=usd (aceita maiúsculas ou minúsculas).
    """
    serializer_class = RegistroCotacaoSerializer

    def get_queryset(self):
        queryset = RegistroCotacao.objects.order_by('-data_hora_consulta', '-id')
        moeda = self.request.query_params.get('moeda')
        if moeda:
            queryset = queryset.filter(moeda_origem=moeda.upper())
        return queryset