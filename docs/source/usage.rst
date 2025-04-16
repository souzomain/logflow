Uso
===

Interface de Linha de Comando
---------------------------

O LogFlow fornece uma interface de linha de comando (CLI) para gerenciar pipelines.

Iniciar uma Pipeline
^^^^^^^^^^^^^^^^^^

Para iniciar o LogFlow com um arquivo de configuração:

.. code-block:: bash

    logflow start --config pipeline.yaml

Verificar o Status
^^^^^^^^^^^^^^^^

Para verificar o status das pipelines em execução:

.. code-block:: bash

    logflow status

Reiniciar uma Pipeline
^^^^^^^^^^^^^^^^^^^

Para reiniciar uma pipeline específica:

.. code-block:: bash

    logflow restart --pipeline webapp-logs

API REST
-------

O LogFlow também fornece uma API REST para gerenciamento programático.

Iniciar o Servidor API
^^^^^^^^^^^^^^^^^^^

Para iniciar o servidor API:

.. code-block:: bash

    python -m logflow.api.routes

Ou usando o script de exemplo:

.. code-block:: bash

    python examples/run_api.py --port 8000

Endpoints da API
^^^^^^^^^^^^^

A API REST permite gerenciar o LogFlow programaticamente:

- ``GET /api/v1/pipelines``: Listar todas as pipelines
- ``POST /api/v1/pipelines``: Criar uma nova pipeline
- ``GET /api/v1/pipelines/{id}``: Obter detalhes de uma pipeline
- ``DELETE /api/v1/pipelines/{id}``: Remover uma pipeline
- ``POST /api/v1/pipelines/{id}/start``: Iniciar uma pipeline
- ``POST /api/v1/pipelines/{id}/stop``: Parar uma pipeline
- ``GET /api/v1/metrics``: Obter métricas do sistema

Exemplo de Uso Programático
-------------------------

O LogFlow também pode ser usado programaticamente em aplicações Python:

.. code-block:: python

    import asyncio
    from logflow.core.engine import Engine

    async def main():
        # Criar uma instância do engine
        engine = Engine()
        
        # Carregar e iniciar uma pipeline
        await engine.load_pipeline("pipeline.yaml")
        await engine.start_pipeline("my-pipeline")
        
        # Aguardar (em uma aplicação real, você faria algo útil aqui)
        await asyncio.sleep(60)
        
        # Parar a pipeline
        await engine.stop_pipeline("my-pipeline")

    if __name__ == "__main__":
        asyncio.run(main())