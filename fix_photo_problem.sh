#!/bin/bash

echo "Création de la migration pour permettre les photos NULL..."
cd /mnt/c/Users/Admin/PycharmProjects/hairbnb_backend
python manage.py makemigrations hairbnb --name="allow_null_photo_profil"

echo "Application de la migration..."
python manage.py migrate

echo "Migration terminée. Votre problème avec les photos devrait être résolu !"
