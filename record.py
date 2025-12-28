import argparse
import json
import queue

import mlx.core as mx
import mlx.nn as nn
import rustymimi
import sentencepiece
import sounddevice as sd
from huggingface_hub import hf_hub_download
from moshi_mlx import models, utils

class Recorder:
    def __init__(self):
        self.is_recording = False
        pass 
    
    @staticmethod
    def create():
        recorder = Recorder()
        recorder.initialize()
        return recorder
    
    def initialize(self):
        self.model_repo = "kyutai/stt-1b-en_fr-mlx"
        self.lm_config = hf_hub_download(self.model_repo, "config.json")
        with open(self.lm_config, "r") as fobj:
            self.lm_config = json.load(fobj)
        mimi_weights = hf_hub_download(self.model_repo, self.lm_config["mimi_name"])
        moshi_name = self.lm_config.get("moshi_name", "model.safetensors")
        moshi_weights = hf_hub_download(self.model_repo, moshi_name)
        tokenizer = hf_hub_download(self.model_repo, self.lm_config["tokenizer_name"])

        self.lm_config = models.LmConfig.from_config_dict(self.lm_config)
        self.model = models.Lm(self.lm_config)
        self.model.set_dtype(mx.bfloat16)
        if moshi_weights.endswith(".q4.safetensors"):
            nn.quantize(self.model, bits=4, group_size=32)
        elif moshi_weights.endswith(".q8.safetensors"):
            nn.quantize(self.model, bits=8, group_size=64)

        print(f"loading model weights from {moshi_weights}")
        if self.model_repo.endswith("-candle"):
            self.model.load_pytorch_weights(moshi_weights, self.lm_config, strict=True)
        else:
            self.model.load_weights(moshi_weights, strict=True)

        print(f"loading the text tokenizer from {tokenizer}")
        self.text_tokenizer = sentencepiece.SentencePieceProcessor(tokenizer)  # type: ignore

        print(f"loading the audio tokenizer {mimi_weights}")
        generated_codebooks = self.lm_config.generated_codebooks
        self.other_codebooks = self.lm_config.other_codebooks
        mimi_codebooks = max(generated_codebooks, self.other_codebooks)
        self.audio_tokenizer = rustymimi.Tokenizer(mimi_weights, num_codebooks=mimi_codebooks)  # type: ignore
    
    def record(self, callback):
        print("warming up the model")
        self.model.warmup()
        gen = models.LmGen(
            model=self.model,
            max_steps=4096,
            text_sampler=utils.Sampler(top_k=25, temp=0),
            audio_sampler=utils.Sampler(top_k=250, temp=0.8),
            check=False,
        )

        block_queue = queue.Queue()
        self.is_recording = True

        def audio_callback(indata, _frames, _time, _status):
            block_queue.put(indata.copy())

        print("recording audio from microphone, speak to get your words transcribed")
        with sd.InputStream(
            channels=1,
            dtype="float32",
            samplerate=24000,
            blocksize=1920,
            callback=audio_callback,
        ):
            first_token = True
            while self.is_recording:
                block = block_queue.get()
                block = block[None, :, 0]
                other_audio_tokens = self.audio_tokenizer.encode_step(block[None, 0:1])
                other_audio_tokens = mx.array(other_audio_tokens).transpose(0, 2, 1)[
                    :, :, :self.other_codebooks
                ]
                text_token = gen.step(other_audio_tokens[0])
                text_token = text_token[0].item()
                audio_tokens = gen.last_audio_tokens()
                _text = None
                if text_token not in (0, 3):
                    _text = self.text_tokenizer.id_to_piece(text_token)  # type: ignore
                    _text = _text.replace("▁", " ")
                    if first_token:
                        _text.strip()
                        first_token = False
                    callback(_text)

    def stop_recording(self):
        self.is_recording = False