#!/bin/bash
# Script de demonstração das novas funcionalidades do LogFlow

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
run_cmd "rm -f /tmp/test.log /tmp/processed.log /tmp/processed.txt /tmp/winlogbeat.json /tmp/windows-events.log"

# Gerar logs de exemplo do Windows
section "Gerando logs de eventos do Windows"
run_cmd "python3 /workspace/logflow/examples/generate_winlogs.py --count 50 --interval 0.01"
run_cmd "head -n 1 /tmp/winlogbeat.json | jq"

# Mostrar a configuração para logs do Windows
section "Configuração para logs do Windows"
run_cmd "cat /workspace/logflow/examples/windows_logs.yaml"

# Executar o LogFlow com a configuração para logs do Windows
section "Executando LogFlow com configuração para logs do Windows"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands start --config examples/windows_logs.yaml &"
run_cmd "sleep 5"  # Dar tempo para o LogFlow processar os logs
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands status"
run_cmd "head -n 1 /tmp/windows-events.log | jq"

# Matar o processo do LogFlow
run_cmd "pkill -f 'python3 -m logflow.cli.commands start'"
run_cmd "sleep 2"

# Demonstrar os novos processadores
section "Novos processadores do LogFlow"
echo -e "${GREEN}Regex Processor:${NC}"
echo "Extrai campos usando expressões regulares:"
echo "pattern: \"User: (?<username>[\\w\\\\]+).*Source: (?<source>[\\w-]+)\""
echo ""

echo -e "${GREEN}Grok Processor:${NC}"
echo "Extrai campos usando padrões Grok (similar ao Logstash):"
echo "patterns: [\"%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}\"]"
echo ""

echo -e "${GREEN}Mutate Processor:${NC}"
echo "Modifica campos (adicionar, remover, renomear, converter, etc.):"
echo "add_fields, remove_fields, rename_fields, uppercase_fields, convert_fields, etc."
echo ""

echo -e "${GREEN}Enrich Processor:${NC}"
echo "Enriquece eventos com dados adicionais:"
echo "lookup, geolocalização, DNS, User-Agent, etc."
echo ""

# Iniciar a interface web
section "Interface Web do LogFlow"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands web --port 8080 &"
run_cmd "sleep 3"

echo -e "${GREEN}Interface web iniciada em:${NC} http://localhost:8080"
echo "A interface web permite:"
echo "- Visualizar o status de todas as pipelines"
echo "- Iniciar e parar pipelines"
echo "- Monitorar métricas de processamento em tempo real"
echo "- Carregar novas configurações"
echo ""
echo "Pressione Enter para continuar..."
read

# Matar o processo da interface web
run_cmd "pkill -f 'python3 -m logflow.cli.commands web'"
run_cmd "sleep 2"

section "Demonstração concluída"
echo -e "${GREEN}Demonstração das novas funcionalidades do LogFlow concluída com sucesso!${NC}"
echo "O LogFlow agora suporta:"
echo "- Logs de eventos do Windows (Winlogbeat)"
echo "- Processadores avançados (regex, grok, mutate, enrich)"
echo "- Interface web para monitoramento"