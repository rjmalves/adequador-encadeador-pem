from idecomp.decomp.dadger import Dadger
from idecomp.decomp.modelos.dadger import RQ
from adequador.utils.backup import converte_utf8, realiza_backup
from adequador.utils.log import Log
from adequador.utils.nomes import dados_caso, nome_arquivo_dadger
from os.path import join


def ajusta_dados_rees(diretorio: str):
    Log.log().info(f"Adequando REES...")

    _, _, revisao_caso = dados_caso(diretorio)
    arquivo = nome_arquivo_dadger(revisao_caso)
    realiza_backup(diretorio, arquivo)

    converte_utf8(diretorio, arquivo)
    dadger = Dadger.read(join(diretorio, arquivo))

    # ===================== Correção para 12 REEs
    # Alterar nó fictício de 5 para 11 no registro SB e DP
    n_est = len(dadger.dp(codigo_submercado=1))

    no_fc = dadger.sb(nome_submercado="FC").codigo_submercado
    if no_fc != 11:
        # Registro SB
        dadger.sb(nome_submercado="FC").codigo_submercado = 11

        # Registro DP
        for e in range(n_est):
            dadger.dp(
                estagio=e + 1, codigo_submercado=no_fc
            ).codigo_submercado = 11

    # Bloco RQ (Vazão defluente mínima histórica):
    # inclusão dos REEs 5 a 12 quando ausentes, considerando 100% da vazão mínima do histórico
    # para os estágios semanais e 0% para o estágio mensal, assim como é feito nos decks atuais.
    vaz = [100] * (n_est - 1) + [0]
    n_rees = 12
    for r in range(n_rees):
        reg = dadger.rq(codigo_ree=r + 1)
        if reg is None:
            rq_novo = RQ()
            rq_novo.codigo_ree = r + 1
            rq_novo.vazao = vaz
            posicao = dadger.data.get_registers_of_type(RQ)[-1]
            dadger.data.add_after(posicao, rq_novo)
        else:
            reg.vazao = vaz

    # Bloco UH
    # Corrigir índice do REE para usinas que nao estao na configuração do NEWAVE
    # O mapeamento indicou apenas Edgard de Souza de 1 (antigo Sudeste) para 10 (Paraná)
    cod_uh = 107
    ree_uh = 10
    if dadger.uh(codigo_usina=cod_uh).codigo_ree is not ree_uh:
        dadger.uh(codigo_usina=cod_uh).codigo_ree = ree_uh

    dadger.write(join(diretorio, arquivo))
