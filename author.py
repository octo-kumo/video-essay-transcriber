import json
import os

from PIL.Image import fromarray


def generate_md(title, text, images):
    content = "# " + title
    if not os.path.exists(title): os.mkdir(title)
    text = process_text(text)
    for i, (t, f) in enumerate(images):
        with open(os.path.join(title, f"{i}.png")) as file:
            fromarray(f).save(file)
    for section in text:
        content += section.text + "\n\n"
    content += '\n\n'.join([os.path.join(title, f"{i}.png") for i in range(len(images))])
    return content


def process_text(text):
    return [{"start": section['result'][0]['start'], "end": section['result'][-1]['end'], "text": section['text']} for
            section in text if 'result' in section]
