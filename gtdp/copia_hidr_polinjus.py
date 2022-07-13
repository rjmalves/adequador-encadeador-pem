from os.path import join
from shutil import copyfile

# Dados de entrada
DIR_HIDR = "/home/pem/estudos/CPAMP/Ciclo_2021-2022/consistencia_decks/dados_gtdp/hidr.dat"
DIR_POLINJUS = "/home/pem/estudos/CPAMP/Ciclo_2021-2022/consistencia_decks/dados_gtdp/polinjus.dat"


def copia_arquivos_gtdp(caso: str,diretorio: str,DIR_HIDR,DIR_POLINJUS):

    rv = caso.split("_rv")[1]

    arq_destino_hidr = join(diretorio,"decomp", "hidr.dat")
    arq_destino_polinjus = join(diretorio,"decomp" "polinjus.dat")
    # copia para a pasta do deck
    copyfile(DIR_HIDR, arq_destino_hidr)
    copyfile(DIR_POLINJUS, arq_destino_polinjus)

    if rv == 0:
        arq_destino_hidr = join(diretorio,"newave", "hidr.dat")
        # copia para a pasta do deck
        copyfile(DIR_HIDR, arq_destino_hidr)


