from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import RQ
from adequador.utils.backup import converte_utf8, realiza_backup
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso, nome_arquivo_dadger


def ajusta_dados_rees(diretorio: str):

    Log.log().info(f"Adequando REES...")

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    realiza_backup(diretorio, arquivo)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.le_arquivo(diretorio, arquivo)

    # ===================== Correção para 12 REEs
    # Alterar nó fictício de 5 para 11 no registro SB e DP
    n_est = len(dadger.dp(subsistema=1))

    no_fc = dadger.sb(nome="FC").codigo
    if no_fc != 11:
        # Registro SB
        dadger.sb(nome="FC").codigo = 11

        # Registro DP
        for e in range(n_est):
            dadger.dp(estagio=e + 1, subsistema=no_fc).subsistema = 11

    # Bloco RQ (Vazão defluente mínima histórica):
    # inclusão dos REEs 5 a 12 quando ausentes, considerando 100% da vazão mínima do histórico
    # para os estágios semanais e 0% para o estágio mensal, assim como é feito nos decks atuais.
    vaz = [100] * (n_est - 1) + [0]
    n_rees = 12
    for r in range(n_rees):
        reg = dadger.rq(ree=r + 1)
        if reg is None:
            rq_novo = RQ()
            rq_novo.ree = r + 1
            rq_novo.vazoes = vaz
            posicao = dadger.lista_registros(RQ)[-1]
            dadger.cria_registro(posicao, rq_novo)
        else:
            reg.vazoes = vaz

    # Bloco UH
    # Corrigir índice do REE para usinas que nao estao na configuração do NEWAVE
    # O mapeamento indicou apenas Edgard de Souza de 1 (antigo Sudeste) para 10 (Paraná)
    cod_uh = 107
    ree_uh = 10
    if dadger.uh(codigo=cod_uh).ree is not ree_uh:
        dadger.uh(codigo=cod_uh).ree = ree_uh

    dadger.escreve_arquivo(diretorio, arquivo)
