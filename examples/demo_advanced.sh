#!/bin/bash
# Script de demonstração avançada do LogFlow

# Definir cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sem cor

# Função para imprimir cabeçalhos de seção
section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Função para executar um comando com descrição
run_cmd() {
    echo -e "${YELLOW}$ $1${NC}"
    eval "$1"
    echo ""
}

# Limpar arquivos existentes
section "Limpando ambiente"
run_cmd "rm -f /tmp/test.log /tmp/processed.log /tmp/processed.txt /tmp/errors.log"

# Gerar logs de exemplo
section "Gerando logs de exemplo"
run_cmd "python3 /workspace/logflow/examples/generate_logs.py --count 100 --interval 0.01"
run_cmd "head -n 3 /tmp/test.log"

# Mostrar a configuração avançada
section "Configuração avançada"
run_cmd "cat /workspace/logflow/examples/advanced.yaml"

# Explicar os novos componentes
section "Novos componentes do LogFlow"
echo -e "${GREEN}Fontes (Sources):${NC}"
echo "- file: Lê logs de arquivos locais"
echo "- kafka: Consome logs de tópicos do Apache Kafka"
echo "- s3: Lê logs de buckets do Amazon S3"
echo ""
echo -e "${GREEN}Processadores (Processors):${NC}"
echo "- json: Analisa dados JSON e extrai campos"
echo "- filter: Filtra eventos com base em condições configuráveis"
echo ""
echo -e "${GREEN}Destinos (Sinks):${NC}"
echo "- file: Escreve logs em arquivos locais"
echo "- elasticsearch: Envia logs para o Elasticsearch"
echo "- opensearch: Envia logs para o OpenSearch"
echo "- s3: Armazena logs em buckets do Amazon S3"
echo ""

# Executar o LogFlow com a configuração simples
section "Executando LogFlow com configuração simples"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands start --config examples/simple.yaml &"
run_cmd "sleep 5"  # Dar tempo para o LogFlow processar os logs
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands status"
run_cmd "head -n 3 /tmp/processed.log"

# Matar o processo do LogFlow
run_cmd "pkill -f 'python3 -m logflow.cli.commands start'"
run_cmd "sleep 2"

# Mostrar como seria a integração com serviços em nuvem
section "Integração com serviços em nuvem"
echo -e "${GREEN}Exemplo de configuração para integração com Kafka, S3 e OpenSearch:${NC}"
run_cmd "cat /workspace/logflow/examples/cloud_integration.py | grep -A 50 'CLOUD_CONFIG = {'"

section "Uso simplificado dos componentes"
echo -e "${GREEN}Antes:${NC}"
echo "type: \"FileSource\""
echo "type: \"JsonProcessor\""
echo "type: \"FilterProcessor\""
echo "type: \"FileSink\""
echo "type: \"ElasticsearchSink\""
echo ""
echo -e "${GREEN}Agora:${NC}"
echo "type: \"file\""
echo "type: \"json\""
echo "type: \"filter\""
echo "type: \"file\""
echo "type: \"elasticsearch\""
echo "type: \"opensearch\""
echo "type: \"s3\""
echo ""

section "Demonstração concluída"
echo -e "${GREEN}Demonstração avançada do LogFlow concluída com sucesso!${NC}"
echo "O LogFlow agora suporta:"
echo "- Kafka como fonte de dados"
echo "- S3 como fonte e destino"
echo "- OpenSearch como destino para pesquisa"
echo "- Nomes simplificados para todos os componentes"