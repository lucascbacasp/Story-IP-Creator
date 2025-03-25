# Story IP Creator

Un agente para crear y mintear activos IP (propiedad intelectual) en la red de Story usando inteligencia artificial.

## Descripción

`Story-IP-Creator` es un proyecto que permite generar imágenes con DALL-E, subirlas a IPFS (InterPlanetary File System) y registrarlas como activos IP en la testnet de Story. Este agente automatiza el proceso de creación de activos digitales, desde la generación de imágenes hasta el minteo de tokens de licencia, integrando tecnologías como IA, blockchain e IPFS.

### Características principales
- Generación de imágenes con DALL-E a partir de un prompt del usuario.
- Subida de imágenes a IPFS para almacenamiento descentralizado.
- Creación de metadatos para el activo IP.
- Minteo y registro del activo IP en la red de Story con términos de licencia.
- Minteo de tokens de licencia asociados al activo IP.

## Requisitos

Para usar este proyecto, necesitas:

- **Python 3.8 o superior** instalado en tu máquina.
- Un entorno virtual (recomendado) para gestionar dependencias.
- Una clave de API de OpenAI para usar DALL-E.
- Acceso a la testnet de Story (necesitas una clave privada y una URL de RPC).
- Un servidor local (como el proporcionado en `server.py`) corriendo en `http://127.0.0.1:8000`.

### Dependencias
Las siguientes bibliotecas de Python son necesarias. Están incluidas en el proyecto, pero puedes instalarlas manualmente si es necesario:

- `requests`
- `asyncio`
- `python-dotenv`
- `langchain-community` (para usar DALL-E)

## Instalación

1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/lucascbacasp/Story-IP-Creator.git
   cd Story-IP-Creator# Story IP Creator Agent

A LangGraph-based agent for creating, minting, and registering IP assets with Story.


This agent helps users create AI-generated images, upload them to IPFS, and register them as IP assets on the Story blockchain.
=== Process Complete ===
Your IP has been successfully created and registered with Story!
```

The agent handles all the complex interactions with DALL-E for image generation, IPFS for storage, and the Story blockchain for minting and registration.
