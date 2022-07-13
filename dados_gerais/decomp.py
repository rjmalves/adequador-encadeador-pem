from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import TE, EV, SB, CQ, EA, ES, QI


def ajusta_dados_gerais(diretorio: str, arquivo: str):

    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # Certifica que existe registro TE
    if dadger.te.titulo is None:
        te_novo = TE()
        te_novo.titulo = (
            "PMO"  # Título provisório depois será alterado pelo encadeador
        )
        reg_anterior = dadger.lista_registros(SB)[0]
        dadger.cria_registro(reg_anterior, te_novo)

    # Consideração de evaporação linear com base no volume inicial
    if dadger.ev is None:
        ev_novo = EV()
        ev_novo.modelo = 1
        ev_novo.volume_referencia = "INI"
        reg_anterior = dadger.lista_registros(CQ)[-1]
        dadger.cria_registro(reg_anterior, ev_novo)
    else:
        dadger.ev.modelo = 1
        dadger.ev.volume_referencia = "INI"

    # Exclusão de registros antigos
    # Registro EA e ES, referentes a energia afluente passada mensal e semanal, foram descontinuados
    # nos casos atuais, pois as informações passaram a ser lidas no arquivo vazoes.xx.
    # Registro QI, referente a vazões incrementais passadas necessárias para consideração do
    # tempo de viagem no cálculo da energia natural afluente, foi descontinuado nos casos atuais,
    # pois a informação agora é lida pelo vazoes.xx.

    def exclui_registros(dadger: Dadger, registros):
        if len(registros) > 0:
            for reg in registros:
                dadger.deleta_registro(reg)

    registro_ea = dadger.lista_registros(EA)
    registro_es = dadger.lista_registros(ES)
    registro_qi = dadger.lista_registros(QI)

    exclui_registros(dadger,registro_ea)
    exclui_registros(dadger,registro_es)
    exclui_registros(dadger,registro_qi)

    dadger.escreve_arquivo(diretorio, arquivo)
