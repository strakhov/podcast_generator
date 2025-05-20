Запуск сервиса:

- в папку langflow положить podcast-generator-458516-be67f9964d96.json с ключами доступа к google.cloud

- в этой же папке выполнить
docker-compose up

Интерфейс доступен по http://localhost:8501/
Langflow работает на http://localhost:7860/



mv /mnt/c/Users/Xiaomi/Desktop/Oleg/Docs/ML/Podcast_generator/podcast_generator.pem ~/

chmod 600 ~/podcast_generator.pem

ssh -i ~/podcast_generator.pem ubuntu@ec2-54-196-201-143.compute-1.amazonaws.com



sudo docker-compose up -d --build