from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import TE, EV, SB, CQ, EA, ES, QI
from adequador.utils.backup import converte_utf8
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso, nome_arquivo_dadger
from os.path import join


def ajusta_dados_gerais(diretorio: str):
    Log.log().info(f"Adequando DADOSGERAIS...")

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # Certifica que existe registro TE
    if dadger.te is None:
        te_novo = TE()
        te_novo.titulo = (
            "PMO"  # Título provisório depois será alterado pelo encadeador
        )
        dadger.data.preppend(te_novo)

    # Consideração de evaporação linear com base no volume inicial
    if dadger.ev is None:
        ev_novo = EV()
        ev_novo.modelo = 1
        ev_novo.volume_referencia = "INI"
        dadger.data.append(ev_novo)
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
                dadger.data.remove(reg)

    registro_ea = dadger.data.get_registers_of_type(EA)
    registro_es = dadger.data.get_registers_of_type(ES)
    registro_qi = dadger.data.get_registers_of_type(QI)

    exclui_registros(dadger, registro_ea)
    exclui_registros(dadger, registro_es)
    exclui_registros(dadger, registro_qi)

    dadger.write(join(diretorio, arquivo))
