import pathlib
from os.path import join
from dotenv import load_dotenv
from adequador.decomp import adequa_decomp
from adequador.newave import adequa_newave
from adequador.utils.log import Log


DIR_BASE = pathlib.Path().resolve()
Log.configura_logging(DIR_BASE)

load_dotenv(join(DIR_BASE, "adequa.cfg"), override=True)

adequa_newave()
adequa_decomp()
