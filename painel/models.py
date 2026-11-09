from django.db import models


class RegistroCotacao(models.Model):
    moeda_origem = models.CharField(max_length=5, default='USD')
    moeda_destino = models.CharField(max_length=5, default='BRL')
    # 14 dígitos com 4 casas: comporta até 9.999.999.999,9999 (o BTC passa de R$ 500 mil).
    valor = models.DecimalField(max_digits=14, decimal_places=4)
    data_hora_consulta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_hora_consulta', '-id']

    def __str__(self):
        return f'{self.moeda_origem}/{self.moeda_destino} = {self.valor}'