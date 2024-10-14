#! /bin/bash

# Create the .env files for each service

# MongoDB
cp ./mongodb/.env.example ./mongodb/.env

# Weaviate
cp ./weaviate/.env.example ./weaviate/.env

# Supabase
cp ./supabase/.env.example ./supabase/.env

# Unstructured
cp ./unstructured/.env.example ./unstructured/.env

# Stackweb
cp ./stackweb/.env.example ./stackweb/.env

# Stackend
cp ./stackend/.env.example ./stackend/.env

# Stackrepl
cp ./stackrepl/.env.example ./stackrepl/.env

# Caddy
cp ./caddy/.env.example ./caddy/.env
