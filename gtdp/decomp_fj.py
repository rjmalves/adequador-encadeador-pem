from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import CQ, FJ

# Dados de entrada:
nome_arq_polinjus = "polinjus.dat"

def ajusta_fj(diretorio: str, arquivo: str, nome_arq_polinjus):
    
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # Consideração dos polinômios de jusante
    if dadger.fj.arquivo is None:
        fj_novo = FJ()
        fj_novo.arquivo = nome_arq_polinjus
        reg_anterior = dadger.lista_registros(CQ)[-1]
        dadger.cria_registro(reg_anterior,fj_novo)
    else:
        dadger.fj.arquivo = nome_arq_polinjus


    dadger.escreve_arquivo(diretorio, arquivo)



