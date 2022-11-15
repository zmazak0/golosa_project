import os
from redis import Redis
import json
# from fairseq.checkpoint_utils import load_model_ensemble_and_task_from_hf_hub
# from fairseq.models.text_to_speech.hub_interface import TTSHubInterface
import torchaudio
import torch
from dotenv import load_dotenv
from pathlib import Path

# ЭТАП 1
import torch
from pprint import pprint
from omegaconf import OmegaConf
from IPython.display import Audio, display

# ЭТАП 2
torch.hub.download_url_to_file('https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml',
                               'latest_silero_models.yml',
                               progress=False)
models = OmegaConf.load('latest_silero_models.yml')

# ЭТАП 3
# see latest avaiable models
available_languages = list(models.tts_models.keys())
print(f'Available languages {available_languages}')

for lang in available_languages:
    _models = list(models.tts_models.get(lang).keys())
    print(f'Available models for {lang}: {_models}')

# ЭТАП 4

import torch

language = 'ru'
model_id = 'v3_1_ru'
device = torch.device('cpu')

model, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language=language,
                                     speaker=model_id)
model.to(device)  # gpu or cpu

# ЭТАП 5 ПАРАМЕТРЫ
sample_rate = 48000
speaker = 'xenia'
put_accent=True
put_yo=True

if Path("../.env").is_file():
    load_dotenv("../.env")
REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
REDIS_PORT = int(os.environ['REDIS_PORT'])


redis_client = Redis(host=REDIS_HOSTNAME, port=REDIS_PORT, db=0)
redis_subscriber = redis_client.pubsub()
redis_subscriber.subscribe("text")

while True:
    message = redis_subscriber.get_message()
    if message and message['type'] == "message":
        channel = message['channel'].decode("utf-8")
        request = json.loads(message['data'].decode("utf-8"))
        print("Input:", request)
        if channel == "text":
            # sample = TTSHubInterface.get_model_input(task, request['text'])
            # waveform, sample_rate = TTSHubInterface.get_prediction(task, models[0], generator, sample)

            audio = model.apply_tts(text=request['text'],
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=put_accent,
                                    put_yo=put_yo)
            torchaudio.save('response.mp3', torch.unsqueeze(audio, 0), sample_rate, format='mp3')
            with open("response.mp3", 'rb') as f:
                response = {
                    'audio': list(f.read()),
                    'chat_id': request['chat_id']
                }
                print("Output:", response)
                redis_client.publish(channel="audio", message=json.dumps(response))
            os.remove("response.mp3")