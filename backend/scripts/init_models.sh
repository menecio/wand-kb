#!/bin/sh
set -e

# Pull the embedding and generation models used by the knowledge base.
# Set OLLAMA_HOST to point at the running Ollama service if not using the default.

ollama pull nomic-embed-text
ollama pull qwen2.5:3b
