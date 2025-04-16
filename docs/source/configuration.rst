Configuração
============

LogFlow utiliza arquivos YAML para configuração. Um exemplo básico:

.. code-block:: yaml

    name: "simple-pipeline"

    sources:
      - name: "test-file"
        type: "file"
        config:
          path: "/tmp/test.log"
          tail: true
          read_from_start: true

    processors:
      - name: "json-parser"
        type: "json"
        config:
          field: "raw_data"
          target_field: "parsed"
          preserve_original: true
          ignore_errors: true

      - name: "filter-debug"
        type: "filter"
        config:
          condition: "level != 'DEBUG'"
          mode: "all"

    sinks:
      - name: "file-output"
        type: "file"
        config:
          path: "/tmp/processed.log"
          format: "json"
          append: true

    batch_size: 100
    batch_timeout: 5.0

Estrutura de Configuração
-----------------------

A configuração de uma pipeline é composta pelos seguintes elementos:

- ``name``: Nome da pipeline
- ``sources``: Lista de fontes de dados
- ``processors``: Lista de processadores (opcional)
- ``sinks``: Lista de destinos
- ``batch_size``: Tamanho do lote para processamento em batch (opcional, padrão: 100)
- ``batch_timeout``: Tempo máximo em segundos para processar um lote (opcional, padrão: 5.0)

Configuração de Sources
---------------------

Cada source (fonte) é configurado com os seguintes campos:

- ``name``: Nome da fonte
- ``type``: Tipo da fonte (classe do plugin)
- ``config``: Configuração específica da fonte

Exemplo de configuração para fonte de arquivo (``file``):

.. code-block:: yaml

    sources:
      - name: "log-file"
        type: "file"
        config:
          path: "/var/log/app.log"
          tail: true
          read_from_start: false
          poll_interval: 1.0

Exemplo de configuração para fonte Kafka (``kafka``):

.. code-block:: yaml

    sources:
      - name: "kafka-logs"
        type: "kafka"
        config:
          brokers: ["kafka1:9092", "kafka2:9092"]
          topics: ["logs", "events"]
          group_id: "logflow-consumer"
          auto_offset_reset: "latest"
          max_poll_records: 500

Exemplo de configuração para fonte S3 (``s3``):

.. code-block:: yaml

    sources:
      - name: "s3-logs"
        type: "s3"
        config:
          bucket: "my-logs-bucket"
          prefix: "app-logs/"
          region: "us-east-1"
          poll_interval: 300.0  # 5 minutos

Configuração de Processors
------------------------

Cada processor (processador) é configurado com os seguintes campos:

- ``name``: Nome do processador
- ``type``: Tipo do processador (classe do plugin)
- ``config``: Configuração específica do processador

Exemplo de configuração para processador JSON (``json``):

.. code-block:: yaml

    processors:
      - name: "parse-json"
        type: "json"
        config:
          field: "raw_data"
          target_field: "parsed"
          preserve_original: true
          ignore_errors: true

Exemplo de configuração para processador de filtro (``filter``):

.. code-block:: yaml

    processors:
      - name: "filter-errors"
        type: "filter"
        config:
          condition: "level in [ERROR, CRITICAL]"
          mode: "all"
          negate: false

Configuração de Sinks
-------------------

Cada sink (destino) é configurado com os seguintes campos:

- ``name``: Nome do destino
- ``type``: Tipo do destino (classe do plugin)
- ``config``: Configuração específica do destino

Exemplo de configuração para destino de arquivo (``file``):

.. code-block:: yaml

    sinks:
      - name: "output-file"
        type: "file"
        config:
          path: "/var/log/processed.log"
          format: "json"
          append: true

Exemplo de configuração para destino Elasticsearch (``elasticsearch``):

.. code-block:: yaml

    sinks:
      - name: "es-output"
        type: "elasticsearch"
        config:
          hosts: ["https://elasticsearch:9200"]
          index: "logs-{yyyy.MM.dd}"
          username: "elastic"
          password: "changeme"
          ssl_verify: true

Exemplo de configuração para destino OpenSearch (``opensearch``):

.. code-block:: yaml

    sinks:
      - name: "opensearch-output"
        type: "opensearch"
        config:
          hosts: ["https://opensearch:9200"]
          index: "logs-{yyyy.MM.dd}"
          username: "admin"
          password: "admin"
          ssl_verify: false

Exemplo de configuração para destino S3 (``s3``):

.. code-block:: yaml

    sinks:
      - name: "s3-archive"
        type: "s3"
        config:
          bucket: "logs-archive"
          key_prefix: "processed-logs"
          region: "us-east-1"
          format: "json"
          buffer_size: 52428800  # 50 MB
