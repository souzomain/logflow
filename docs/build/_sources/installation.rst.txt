Instalação
===========

Requisitos
---------

- Python 3.9 ou superior
- Poetry

Instalação com Poetry
-------------------

.. code-block:: bash

    # Clonar o repositório
    git clone https://github.com/organization/logflow.git
    cd logflow

    # Instalar dependências
    poetry install

    # Instalar em modo de desenvolvimento
    poetry install --with dev

Instalação com pip
----------------

.. code-block:: bash

    # Instalar do PyPI
    pip install logflow

    # Ou instalar do repositório
    pip install git+https://github.com/organization/logflow.git

Verificação da Instalação
-----------------------

Após a instalação, você pode verificar se o LogFlow está funcionando corretamente executando:

.. code-block:: bash

    logflow --version