from nicegui import ui

with open("code/make_graphs.py") as file:
    exec(file.read())

with ui.tabs().classes('w-full') as tabs:
    one = ui.tab('Chi Distribution')
    two = ui.tab('RS Mean Boxplot')
    three = ui.tab('Sample Pair Graphs')
    four = ui.tab('Suspicious Score Graphs')
with ui.tab_panels(tabs, value=one).classes('w-full'):
    with ui.tab_panel(one):
        with ui.row().classes('w-full justify-center'):
            ui.image('results/graphs/chi_mean_distribution.png').classes('w-200')
    with ui.tab_panel(two):
        with ui.row().classes('w-full justify-center'):
            ui.image('results/graphs/rs_mean_boxplot.png').classes('w-200')
    with ui.tab_panel(three):
        with ui.row().classes('w-full items-center justify-center gap-4'):
            ui.image('results/graphs/sample_pair_deviation.png').classes('w-150')
            ui.image('results/graphs/sample_pair_equal_ratio.png').classes('w-150')
    with ui.tab_panel(four):
        with ui.row().classes('w-full items-center justify-center gap-4'):
            ui.image('results/graphs/suspicious_score_boxplot.png').classes('w-150')
            ui.image('results/graphs/suspicious_score_hist.png').classes('w-150')

ui.run()