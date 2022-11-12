import os
import wave
import json

import ffmpeg
import librosa
import numpy as np
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from tqdm import tqdm
from vosk import Model, KaldiRecognizer

from author import generate_md
from frame_analyzer import keyFrame
from selector import select_images

model = Model("models/vosk-model-en-us-0.22-lgraph", lang="en-us")

import pytube.request

pytube.request.default_range_size = 1024 * 1024


# model = Model(lang="en-us")


async def analyze_yt(link, window=None, verbose=False):
    bar = tqdm(total=0)

    def progress_func(self, chunk, bytes_remaining):
        print(self.filesize, bytes_remaining)
        window['load-progress'].UpdateBar(self.filesize - bytes_remaining, self.filesize)
        bar.total = self.filesize
        bar.update(len(chunk))

    try:
        yt = YouTube(link, on_progress_callback=progress_func)
        print(yt.title)

        outfile = yt.streams.filter(progressive=True, file_extension='mp4').order_by(
            'resolution').desc().first().download(
            "download", filename=f"{yt.video_id}.mp4", timeout=5000, skip_existing=window['skip_existing'].Get())
        print(f"downloaded video to {outfile}")
        return yt.title, await analyze_video(outfile, window=window, verbose=verbose)
    except VideoUnavailable:
        print(f'Video {link} is unavaialable, skipping.')
    except Exception as e:
        print(f"{e}")


async def analyze_video(video, window=None, verbose=False):
    print("analyze_video", video)
    window['load-progress'].UpdateBar(0, 3)
    audio = prep_audio(video)
    window['load-progress'].UpdateBar(1, 3)
    title = os.path.basename(video)
    text = analyze_audio(audio, window=window, verbose=verbose)
    print("analyzed audio: ", text)
    kf = keyFrame(video, window)
    print("keyFrame: ", text)
    cl = kf.get_clusters()
    selection = select_images(cl)
    print("selection: ", selection)
    images = kf.get_frames(selection)
    md = generate_md(title, text, images)
    window['markdown'].update(md)


def prep_audio(video):
    audio_track = video.replace(".mp4", ".wav")
    input = ffmpeg.input(video)
    stream = ffmpeg.output(input.audio, audio_track, ac=1)
    ffmpeg.run(stream, overwrite_output=True)
    return audio_track


def analyze_audio(audio, window=None, verbose=False):
    print(analyze_audio, audio)
    global bar
    wf = wave.open(audio, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)

    # get the list of JSON dictionaries
    results = []
    # recognize speech using vosk model
    window['load-progress'].UpdateBar(3, 3)
    if os.path.exists(audio.replace(".wav", ".json")):
        with open(audio.replace(".wav", ".json"), 'r') as f:
            results = json.load(f)
        if window: window['trans-progress'].UpdateBar(1, 1)
    else:
        c = 0
        if verbose: bar = tqdm(total=wf.getnframes())
        while True:
            data = wf.readframes(4000)
            c += 4000
            if verbose: bar.update(4000)
            if len(data) == 0:
                break
            if window: window['trans-progress'].UpdateBar(c, wf.getnframes())
            if rec.AcceptWaveform(data):
                part_result = json.loads(rec.Result())
                results.append(part_result)
                if window: window['preview'].update('\n'.join([l['text'] for l in results if 'text' in l]))
            # else:
            #     results.append(json.load(rec.PartialResult()))

        part_result = json.loads(rec.FinalResult())
        results.append(part_result)
        with open(audio.replace(".wav", ".json"), "w") as f:
            json.dump(results, f)
    text = '\n'.join([l['text'] for l in results if 'text' in l])
    if window: window['preview'].update(text)
    wf.close()  # close audiofile
    return results


def get_sections(audio):
    x, sr = librosa.load(audio)
    x = librosa.to_mono(x)
    n_fft = 2048
    S = librosa.stft(x, n_fft=n_fft, hop_length=n_fft // 2)
    D = np.abs(librosa.amplitude_to_db(np.abs(S), ref=np.max))
    sections = librosa.effects.split(x, top_db=np.median(D) - 5)
    return sections
