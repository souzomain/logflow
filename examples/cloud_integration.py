#!/usr/bin/env python3
"""
Exemplo de integração do LogFlow com serviços em nuvem.

Este script demonstra como configurar e usar o LogFlow com:
- Kafka como fonte de dados
- S3 como fonte e destino
- OpenSearch como destino para pesquisa
"""
import asyncio
import logging
import os
import sys
import signal

from logflow.core.engine import Engine
from logflow.core.config import validate_pipeline_config


# Configuração de exemplo para integração com serviços em nuvem
CLOUD_CONFIG = {
    "name": "cloud-integration",
    "sources": [
        {
            "name": "kafka-logs",
            "type": "kafka",
            "config": {
                "brokers": ["localhost:9092"],
                "topics": ["application-logs"],
                "group_id": "logflow-consumer",
                "auto_offset_reset": "latest"
            }
        },
        {
            "name": "s3-logs",
            "type": "s3",
            "config": {
                "bucket": "my-logs-bucket",
                "prefix": "raw-logs/",
                "region": "us-east-1",
                "poll_interval": 300.0
            }
        }
    ],
    "processors": [
        {
            "name": "json-parser",
            "type": "json",
            "config": {
                "field": "raw_data",
                "target_field": "",
                "preserve_original": True,
                "ignore_errors": True
            }
        },
        {
            "name": "filter-debug",
            "type": "filter",
            "config": {
                "condition": "level != 'DEBUG'",
                "mode": "all"
            }
        }
    ],
    "sinks": [
        {
            "name": "opensearch-output",
            "type": "opensearch",
            "config": {
                "hosts": ["https://opensearch:9200"],
                "index": "logs-{yyyy.MM.dd}",
                "username": "admin",
                "password": "admin",
                "ssl_verify": False
            }
        },
        {
            "name": "s3-archive",
            "type": "s3",
            "config": {
                "bucket": "logs-archive",
                "key_prefix": "processed-logs",
                "region": "us-east-1",
                "format": "json"
            }
        }
    ],
    "batch_size": 500,
    "batch_timeout": 10.0
}


async def run_cloud_integration():
    """Executa a integração com serviços em nuvem."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )
    
    # Validar a configuração
    validate_pipeline_config(CLOUD_CONFIG)
    
    # Criar o engine
    engine = Engine()
    
    # Configurar tratamento de sinais
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(engine.stop())
        )
    
    try:
        # Carregar a pipeline a partir da configuração em memória
        logging.info("Carregando pipeline de integração com nuvem")
        
        # Criar um arquivo temporário com a configuração
        config_path = "/tmp/cloud_integration.yaml"
        with open(config_path, "w") as f:
            import yaml
            yaml.dump(CLOUD_CONFIG, f)
        
        # Carregar a pipeline
        pipeline = await engine.load_pipeline(config_path)
        
        # Iniciar a pipeline
        logging.info(f"Iniciando pipeline: {pipeline.name}")
        await engine.start_pipeline(pipeline.name)
        
        # Manter o script em execução
        logging.info("Pipeline em execução. Pressione Ctrl+C para encerrar.")
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logging.info("Interrompido pelo usuário")
    
    except Exception as e:
        logging.error(f"Erro: {str(e)}", exc_info=True)
    
    finally:
        # Parar o engine
        logging.info("Parando o engine")
        await engine.stop()
        
        # Remover o arquivo temporário
        if os.path.exists(config_path):
            os.unlink(config_path)


if __name__ == "__main__":
    asyncio.run(run_cloud_integration())