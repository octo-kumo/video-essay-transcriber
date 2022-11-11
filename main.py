import PySimpleGUI as sg

from oracle import analyze_yt, analyze_video

sg.theme('DefaultNoMoreNagging')  # Add a touch of color
# All the stuff inside your window.
layout = [[sg.Text("Youtube Link"), sg.InputText(tooltip="Youtube Link")],
          [sg.Text("Video File"), sg.FileBrowse('file', enable_events=True, file_types=(("Video Files", "*.mp4"),))],
          [sg.ProgressBar(100, size=(30, 20), key='progress')],
          [sg.Button('Ok'), sg.Button('Cancel')]]

# Create the Window
window = sg.Window('Window Title', layout)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break

    if event == 'Ok':
        if values[0]:
            res = analyze_yt(values[0], progbar=window['progress'], verbose=True)
        else:
            res = analyze_video(values['file'], progbar=window['progress'], verbose=True)
window.close()
