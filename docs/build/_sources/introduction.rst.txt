Introdução
===========

Visão Geral
-----------

LogFlow é uma aplicação ETL (Extração, Transformação e Carregamento) especializada em processamento de logs, inspirada em ferramentas como Graylog e Logstash. A aplicação é capaz de receber logs de múltiplas fontes, processá-los através de transformações configuráveis e encaminhá-los para diferentes destinos de armazenamento ou análise.

Objetivos Principais
-------------------

- Fornecer uma plataforma extensível para processamento de logs
- Suportar diversas fontes de dados e destinos através de plugins
- Permitir transformações e enriquecimento de dados configuráveis
- Garantir alta performance e confiabilidade no processamento
- Facilitar a observabilidade do sistema e dos dados processados

Arquitetura
-----------

A arquitetura do LogFlow é baseada em uma estrutura modular de plugins, dividida em três componentes principais:

1. **Sources (Fontes)**: Plugins responsáveis pela obtenção dos logs de diferentes origens.
2. **Processors (Processadores)**: Componentes que processam, filtram e transformam os dados de log.
3. **Sinks (Destinos)**: Plugins responsáveis pelo envio dos logs processados para os destinos finais.

Fluxo de Processamento
---------------------

O fluxo de processamento no LogFlow segue estas etapas:

1. **Coleta**: Os plugins de fonte coletam logs brutos de suas respectivas origens
2. **Ingestão**: Os logs coletados são convertidos para o formato interno ``LogEvent``
3. **Processamento**: Os logs passam pelos processadores configurados na pipeline
4. **Encaminhamento**: Os logs processados são enviados aos destinos configurados