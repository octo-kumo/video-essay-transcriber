from io import BytesIO

import PySimpleGUI as sg
from PIL.Image import fromarray

from frame_analyzer import keyFrame

sg.theme('DefaultNoMoreNagging')


def array_to_data(array):
    im = fromarray(array).resize((112, 112))
    with BytesIO() as output:
        im.save(output, format="PNG")
        data = output.getvalue()
    return data


def select_images(clusters):
    select_images_tabs = [[sg.Tab(f'#{idx + 1}', [
        [sg.Text("Select Objects to Exclude")],
        [sg.Frame(f"Image {i + 1}", [
            [sg.Image(size=(112, 112), background_color='green', key=f"img{i}", data=array_to_data(clusters[idx][i]))],
        ]) for i in range(5)],
        [sg.Radio("Include", f"radio-g-{idx}", key=idx), sg.Radio("Exclude", f"radio-g-{idx}", default=True)],
        [sg.Button("Prev Batch", key=lambda x=idx - 1: window['tabgroup'].Widget.select(x), disabled=idx == 0),
         sg.Button("Next Batch", key=lambda x=idx + 1: window['tabgroup'].Widget.select(x),
                   disabled=idx == len(clusters) - 1)]
    ], key=f"tab_{idx}") for idx, c in enumerate(clusters)]]
    root = [[sg.TabGroup(select_images_tabs, key="tabgroup")],
            [sg.Button("OK", key='ok'), sg.Button("Cancel (Include All)", key='cancel')]]
    window = sg.Window('Select Images', root)

    while True:
        w, event, values = sg.read_all_windows()
        if event == sg.WIN_CLOSED or event == 'cancel' or event == 'Cancel (Include All)':
            window.close()
            return [False for i in range(len(clusters))]
        if callable(event):
            event()
        if event == "ok" or event == "Ok":
            window.close()
            return [values[i] for i in range(len(clusters))]
    return []

if __name__ == "__main__":
    v = keyFrame("videos/AdamNeely/0ytoUuO-qvg\n.mp4")
    c = v.get_clusters()
    print(c)
    print(select_images(c))
