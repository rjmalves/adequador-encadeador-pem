# Variaveis importantes

CASO=`basename $PWD`
WORKDIR=$PWD
DIR_ADEQUADOR=~/rotinas/adequador-encadeador-pem
ADEQUA=$DIR_ADEQUADOR/main.py

echo Ativando o ambiente virtual
source $DIR_ADEQUADOR/venv/bin/activate

echo Mudando o diretorio para $WORKDIR
cd $WORKDIR

echo Executando o Adequador
python3 $ADEQUA

echo Desativando o ambiente virtual
deactivate

