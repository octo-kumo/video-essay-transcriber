import os
from threading import Thread

import PySimpleGUI as sg
import asyncio
from oracle import analyze_yt, analyze_video

import pytube.request

pytube.request.default_range_size = 1024 * 128


def asyncloop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


loop = asyncio.new_event_loop()
t = Thread(target=asyncloop, args=(loop,))
t.start()


def main():
    sg.theme('DefaultNoMoreNagging')  # Add a touch of color
    # All the stuff inside your window.
    input_file_tab = [[sg.Frame("Youtube Link",
                                [[sg.InputText("https://www.youtube.com/watch?v=XNBP18nrRdw", tooltip="Youtube Link",
                                               key="yt-link"),
                                  sg.Checkbox("Skip Existing", default=True, key="skip_existing")]])],
                      [sg.InputText('', key="file"),
                       sg.FileBrowse("Browse", initial_folder=os.getcwd(), enable_events=True, change_submits=True,
                                     file_types=(("Video Files", "*.mp4"),), key="file_browse")],
                      [sg.Frame("Loading Progress", [[sg.ProgressBar(100, size=(40, 20), key='load-progress')]])],
                      [sg.Button('Load Video', key="load"), sg.Button('Clear', key="clear")]]

    process_file_tab = [
        [sg.Frame("Transcribe Progress", [[sg.ProgressBar(100, size=(40, 20), key='trans-progress')]])],
        [sg.Multiline(size=(60, 10), key='preview')]
    ]

    final_md_tab = [
        [sg.Frame("Frame Analysis Progress", [[sg.ProgressBar(100, size=(40, 20), key='frame-progress')]])],
        [sg.Multiline(size=(60, 10), key='markdown')]
    ]

    root = [[sg.TabGroup([[sg.Tab('Input', input_file_tab, key='input'),
                           sg.Tab('Process', process_file_tab, key='process'),
                           sg.Tab('Final', final_md_tab, key='video')]],
                         selected_title_color='green')]]
    # Create the Window
    window = sg.Window('Window Title', root)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        print(values)
        if event == 'file_browse':
            window['file'].Update(values['file_browse'])
        if event == 'load':
            if values['file']:
                asyncio.run_coroutine_threadsafe(analyze_video(values['file'], window=window, verbose=True), loop)
            else:
                asyncio.run_coroutine_threadsafe(analyze_yt(values['yt-link'], window=window, verbose=True), loop)
        if event == 'clear':
            window['file'].Update('')
            window['yt-link'].Update('')
    window.close()
    loop.call_soon_threadsafe(loop.stop)
    t.join()
    exit(0)


if __name__ == "__main__":
    main()
