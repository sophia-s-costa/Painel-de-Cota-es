# Painel de Cotações — Projeto 4
Painel Django que consulta a cotação USD/BRL na AwesomeAPI,
guarda o histórico no banco e o exibe com fetch().
## Funcionalidades
- /consultar/ busca a cotação e salva um registro
- Tratamento de falhas de rede no servidor e no navegador
- /api/historico/ (JSON, mais recente primeiro)
## Como rodar
1. python -m venv venv e ative o ambiente
2. pip install -r requirements.txt
3. python manage.py migrate
4. python manage.py runserver
## Variáveis de ambiente (opcional)
- COTACAO_URL: troca a URL da API externa
## Prints
(inclua prints do painel e do Admin)
## Autor
Sophia Silva Costa — IESB 2026