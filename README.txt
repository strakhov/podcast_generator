Для запуска:

0.1) В keys.py указать LLM_ENDPOINT, LLM_API_KEY, API_VERSION, MODEL_DEPLOYMENT

0.2) в папке с проектом должен лежать google_creds.json

1) положить в папку input csv-файл со столбцом words, в котором перечислены ключевые слова, идиомы, etc

2) 
docker build -t podcast-generator .

3)
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" podcast-generator

4) забрать готовый подкаст в папке output