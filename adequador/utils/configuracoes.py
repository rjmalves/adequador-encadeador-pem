from adequador.utils.singleton import Singleton
from os import getenv
from os.path import join
import pathlib


class Configuracoes(metaclass=Singleton):
    def __init__(self):
        self.dir_base = pathlib.Path().resolve()
        self.caso_inicio = getenv("CASO_INICIO")
        self.caso_fim = getenv("CASO_FIM")
        self.adequa_newave = bool(int(getenv("ADEQUA_NEWAVE")))
        self.ajustes_newave = getenv("AJUSTES_NEWAVE").split(",")
        self.adequa_decomp = bool(int(getenv("ADEQUA_DECOMP")))
        self.ajustes_decomp = getenv("AJUSTES_DECOMP").split(",")
        self.realiza_backup = bool(int(getenv("REALIZA_BACKUP")))
        self.diretorio_dados_adequacao = join(
            self.dir_base, getenv("DIRETORIO_DADOS_ADEQUACAO")
        )
        self.arquivo_dados_gerais_newave = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_DADOS_GERAIS_NEWAVE"),
        )
        self.arquivo_vminop = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_VMINOP")
        )
        self.arquivo_cfuga_cmont = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_CFUGA_CMONT")
        )
        self.arquivo_cfuga_cmont_historico = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_CFUGA_CMONT_HISTORICO"),
        )
        self.arquivo_ac_nposnw = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_AC_NPOSNW")
        )
        self.arquivo_ac_vertju = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_AC_VERTJU")
        )
        self.arquivo_hidr_fontes_antiga = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_HIDR_FONTES_ANTIGA"),
        )
        self.arquivo_polinjus_fontes_antiga = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_POLINJUS_FONTES_ANTIGA"),
        )
        self.arquivo_hidr_fontes_nova = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_HIDR_FONTES_NOVA")
        )
        self.arquivo_polinjus_fontes_nova = join(
            self.diretorio_dados_adequacao,
            getenv("ARQUIVO_POLINJUS_FONTES_NOVA"),
        )
        self.arquivo_custos_deficit = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_CUSTOS_DEFICIT")
        )
        self.arquivo_volumes_espera = join(
            self.diretorio_dados_adequacao, getenv("ARQUIVO_VOLUMES_ESPERA")
        )
        self.diretorio_vazoes = join(
            self.diretorio_dados_adequacao, getenv("DIRETORIO_VAZOES")
        )
        self.diretorio_velocidades = join(
            self.diretorio_dados_adequacao, getenv("DIRETORIO_VELOCIDADES")
        )
        self.executavel_convertenomes_newave = getenv(
            "EXECUTAVEL_CONVERTENOMES_NEWAVE"
        )
        self.executavel_convertenomes_decomp = getenv(
            "EXECUTAVEL_CONVERTENOMES_DECOMP"
        )
        self.script_converte_codificacao = getenv(
            "SCRIPT_CONVERTE_CODIFICACAO"
        )
