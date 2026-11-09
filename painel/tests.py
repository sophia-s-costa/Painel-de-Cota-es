from decimal import Decimal
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase
from django.urls import reverse

from .models import RegistroCotacao


def resposta_falsa(json_data, status=200):
    r = MagicMock()
    r.json.return_value = json_data
    if status >= 400:
        r.raise_for_status.side_effect = requests.exceptions.HTTPError(f'HTTP {status}')
    return r


# Mesmo formato que a AwesomeAPI devolve para USD-BRL,EUR-BRL,BTC-BRL
DADOS_OK = {
    'USDBRL': {'code': 'USD', 'codein': 'BRL', 'bid': '5.1234'},
    'EURBRL': {'code': 'EUR', 'codein': 'BRL', 'bid': '5.9876'},
    'BTCBRL': {'code': 'BTC', 'codein': 'BRL', 'bid': '612345.5'},
}


class ConsultarCotacaoTest(TestCase):
    @patch('painel.views.requests.get')
    def test_sucesso_salva_uma_linha_por_moeda(self, get):
        get.return_value = resposta_falsa(DADOS_OK)
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Cotações registradas')
        self.assertEqual(RegistroCotacao.objects.count(), 3)
        self.assertEqual(RegistroCotacao.objects.get(moeda_origem='USD').valor, Decimal('5.1234'))
        self.assertEqual(RegistroCotacao.objects.get(moeda_origem='EUR').valor, Decimal('5.9876'))
        self.assertEqual(RegistroCotacao.objects.get(moeda_origem='BTC').valor, Decimal('612345.5'))
        self.assertEqual(get.call_args.kwargs['timeout'], 5)

    @patch('painel.views.requests.get', side_effect=requests.exceptions.Timeout())
    def test_timeout_nao_quebra_a_pagina(self, get):
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Não foi possível consultar')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_erro_http_500_da_api(self, get):
        get.return_value = resposta_falsa({}, status=500)
        r = self.client.get(reverse('consultar'))
        self.assertContains(r, 'Não foi possível consultar')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_formato_inesperado(self, get):
        get.return_value = resposta_falsa({'outra': 'coisa'})
        r = self.client.get(reverse('consultar'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'formato inesperado')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_resposta_vazia(self, get):
        get.return_value = resposta_falsa({})
        r = self.client.get(reverse('consultar'))
        self.assertContains(r, 'formato inesperado')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    @patch('painel.views.requests.get')
    def test_uma_moeda_invalida_nao_grava_nenhuma(self, get):
        dados = dict(DADOS_OK)
        dados['BTCBRL'] = {'code': 'BTC', 'codein': 'BRL'}  # sem o campo bid
        get.return_value = resposta_falsa(dados)
        r = self.client.get(reverse('consultar'))
        self.assertContains(r, 'formato inesperado')
        self.assertEqual(RegistroCotacao.objects.count(), 0)

    def test_template_usa_fetch_e_catch(self):
        with patch('painel.views.requests.get',
                   side_effect=requests.exceptions.ConnectionError()):
            r = self.client.get(reverse('consultar'))
        self.assertContains(r, "fetch('/api/historico/')")
        self.assertContains(r, '.catch(')


class HistoricoAPITest(TestCase):
    def test_ordem_do_mais_recente_ao_mais_antigo(self):
        a = RegistroCotacao.objects.create(valor=Decimal('5.0000'))
        b = RegistroCotacao.objects.create(valor=Decimal('5.1000'))
        c = RegistroCotacao.objects.create(valor=Decimal('5.2000'))
        r = self.client.get(reverse('api-historico'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x['id'] for x in r.json()], [c.id, b.id, a.id])

    def test_somente_leitura(self):
        r = self.client.post(reverse('api-historico'), {'valor': '1'})
        self.assertEqual(r.status_code, 405)

    def test_lista_vazia(self):
        self.assertEqual(self.client.get(reverse('api-historico')).json(), [])

    def test_filtro_por_moeda(self):
        RegistroCotacao.objects.create(moeda_origem='USD', valor=Decimal('5.1'))
        RegistroCotacao.objects.create(moeda_origem='EUR', valor=Decimal('5.9'))
        RegistroCotacao.objects.create(moeda_origem='BTC', valor=Decimal('612345.5'))
        r = self.client.get(reverse('api-historico') + '?moeda=eur')
        self.assertEqual([x['moeda_origem'] for x in r.json()], ['EUR'])