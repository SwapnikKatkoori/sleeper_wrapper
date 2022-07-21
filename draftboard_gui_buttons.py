#!/usr/bin/env python
import pdb
import time

import PySimpleGUI as sg
import csv
import requests
import numpy as np
from pathlib import Path
import json
from sleeper_wrapper import Drafts, League
from fpros import Projections

def TableSimulation():
    """
    Display data in a table format
    """

    sg.popup_quick_message('Hang on for a moment, this will take a bit to create....', auto_close=True,
                           non_blocking=True, font='Default 18')

    sg.set_options(element_padding=(0, 0))

    menu_def = [['File', ['Open', 'Save', 'Exit']],
                ['Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
                ['Help', 'About...'], ]

    MAX_ROWS = 16
    MAX_COL = 12
    BOARD_LENGTH = MAX_ROWS * MAX_COL
    RELIEF_ = "solid"  # "groove" "raised" "sunken" "flat" "ridge"
    BG_COLORS = {"WR": "white on DodgerBlue",
                 "QB": "white on DeepPink",
                 "RB": "white on LimeGreen",
                 "TE": "white on coral",
                 "PK": "white on purple",
                 "DEF": "white on sienna",
                 ".": "white"}

    """
    Get League and user/map
    """
    league = League()
    user_map = league.map_users_to_team_name()
    """
    Get all picks in sleeper draft
    """
    DRAFT_ID = 850087629952249857 # mock
    DRAFT_ID_2022_WEEZ_LEAGUE = 850087629952249857  # 854953046042583040

    draft = Drafts(DRAFT_ID)
    draft_info = draft.get_specific_draft()

    """
    get draft order, map to the user names, and sort by the draft position
    """
    draft_order = draft_info['draft_order']
    draft_order = [{v: user_map[k]} for k, v in draft_order.items()]
    draft_order = sorted(draft_order, key=lambda d: list(d.keys()))
    # ---- draft_order to be used to create labels above the draft board  -----#


    drafted_list = draft.get_all_picks()


    """
    Get ADP Data and list of players, add empty items in the list with for loop to convert  to NP array
    """
    file_path = Path('data/adp/adp.json')
    try:
        adp_response = requests.get(
            url="https://fantasyfootballcalculator.com/api/v1/adp/2qb?teams=12&year=2022&position=all")
        adp_data = adp_response.json()
        with open(file_path, 'w') as data_file:
            json.dump(adp_data, data_file, indent=4)
    except requests.exceptions.RequestException as e:
        with open(file_path, "r") as data_file:
            adp_data = json.load(data_file)
    finally:
        adp_list = adp_data['players']
    adp_list_length = len(adp_list)
    if len(adp_list) > 192:
        for x in range(adp_list_length - BOARD_LENGTH):
            print(f"Removing item: {adp_list.pop(-1)}")
    elif len(adp_list) < 192:
        for x in range(BOARD_LENGTH - adp_list_length):
            adp_list.append({"name": "", "position": ".", "team": ""})

    """
    Create JSON to store/read keepers
    """
    with open('data/keepers/keepers.json', 'r') as keeper_file:
        keeper_list = json.load(keeper_file)
    # removing all keepers in keeper_list from adp_list
    for k in keeper_list:
        k['name'] = f"{k['metadata']['first_name']} {k['metadata']['last_name']}"
        k['position'] = k['metadata']['position']
        k['team'] = k['metadata']['team']
        for i, d in enumerate(adp_list):
            if d['name'].strip() == k['name'].strip():
                k['bye'] = d['bye']
                adp_list.pop(i)
    # sorting the keeper list by the pick
    keeper_list = sorted(keeper_list, key=lambda k: k['pick_no'])
    # inserting all keepers in keeper_list back into adp_list
    for k in keeper_list:
        adp_list.insert(k['pick_no']-1, k)
    # print(keeper_list[0])

    # pdb.set_trace()

    """
    Create draftboard (db) from numpy array of vbd_list
    """
    vbd_prj = Projections()
    vbd_list = vbd_prj.dict
    vbd_list = vbd_list[:192]
    # pdb.set_trace()
    """
    vbd_path = Path("data/vbd/vbd.json")
    with open(vbd_path, "r") as data:
        vbd_list = json.load(data)
    vbd_list = vbd_list[:192]
    """

    db = np.array(adp_list)
    db = np.reshape(db, (16, 12))
    db[1::2, :] = db[1::2, ::-1]

    empty_db = np.empty([16, 12])



    """
    TODO: Map and create right-click menus,
    Sort by ADP or VBD or VOLS or VORP
    Create Keeper method
    """

    filter_tooltip = "Find player"

    # noinspection PyTypeChecker
    column_layout = [[sg.T(f"Rd {str(r + 1)}:", size=(5, 1), justification='left')] +
                     [sg.B(
                         button_text=f"{db[r, c]['name'].split(' ', 1)[0]}\n"
                                     f"{db[r, c]['name'].split(' ', 1)[1]}\n"
                                     f"{db[r, c]['position']} ({db[r, c]['team']}) {db[r, c]['bye']}",
                         enable_events=True,
                         size=(14, 0),
                         p=(0, 0),
                         border_width=1,
                         button_color=BG_COLORS[db[r, c]["position"]],
                         mouseover_colors="gray",
                         highlight_colors=("black", "white"),
                         disabled=False,
                         # changed the disabled_button_color
                         disabled_button_color="white on gray",
                         auto_size_button=False,
                         metadata={"is_clicked": False},
                         key=(r, c)
                     )
                         for c in range(MAX_COL)] for r in range(MAX_ROWS)]
    """
    remove from layout
                   sg.Combo(
                   values=[x['name'] for x in adp_list],
                   default_value=adp_list[0]['name'],
                   readonly=False,
                   size=(14, 10),
                   enable_events=True,
                   k='Keeper Combo'),
               sg.Text('Round'),
               sg.Combo(values=[x + 1 for x in range(16)], default_value=1, key="-Keeper Round-"),
               sg.Text('Pick'),
               sg.Combo(values=[x + 1 for x in range(12)], default_value=1, key="-Keeper Pick-"),
               sg.Button('Set Keeper'),
    # -------FROM SCRATCH-------- #
    col1 = sg.Column([
        [sg.Frame('Draft Board: ', [[sg.T("  ", size=(5, 1), justification='left')] + [sg.B(button_text=draft_order[c+1], border_width=1, key=f"TEAM{c}", size=(14, 0)) for c in range(MAX_COL)]] + \
        [[sg.T(f"Rd {str(r + 1)}:", size=(5, 1), justification='left')] +
                     [sg.B(
                         button_text=f"{db[r, c]['name'].split(' ', 1)[0]}\n"
                                     f"{db[r, c]['name'].split(' ', 1)[1]}\n"
                                     f"{db[r, c]['position']} ({db[r, c]['team']}) {db[r, c]['bye']}",
                         enable_events=True,
                         size=(14, 0),
                         p=(0, 0),
                         border_width=1,
                         button_color=BG_COLORS[db[r, c]["position"]],
                         mouseover_colors="gray",
                         highlight_colors=("black", "white"),
                         disabled=False,
                         # changed the disabled_button_color
                         disabled_button_color="white on gray",
                         auto_size_button=False,
                         metadata={"is_clicked": False},
                         key=(r, c)
                     )
                         for c in range(MAX_COL)] for r in range(MAX_ROWS)])]])
    col2 = sg.Column([
        [sg.Frame("Cheat Sheets: ", [sg.Multiline()])]])
    layout = [[sg.Menu(menu_def)],
              [sg.Text('Weez Draftboard', font='Any 18'),

               sg.Button('Load VBD', key="-Load-VBD-"),
               sg.Button('Load ADP', key="-Load-ADP-"),
               sg.Button('Refresh', key="-Refresh-"),
               sg.Combo(values=[f"{x['metadata']['first_name']} {x['metadata']['last_name']}" for x in drafted_list],
                        size=15,
                        enable_events=True,
                        key="-Drafted-"),
               sg.Text('Search: '),
               sg.Input(key='-Search-', enable_events=True, focus=True, tooltip=filter_tooltip)],
              [col1, col2]]
              # [sg.Col(column_layout, size=(1200, 796), scrollable=True)]]
    
    
    """
    layout = [[sg.Menu(menu_def)],
              [sg.Text('Weez Draftboard', font='Any 18'),

               sg.Button('Load VBD', key="-Load-VBD-"),
               sg.Button('Load ADP', key="-Load-ADP-"),
               sg.Button('Refresh', key="-Refresh-"),
               sg.Combo(values=[f"{x['metadata']['first_name']} {x['metadata']['last_name']}" for x in drafted_list],
                        size=15,
                        enable_events=True,
                        key="-Drafted-"),
               sg.Text('Search: '),
               sg.Input(key='-Search-', enable_events=True, focus=True, tooltip=filter_tooltip)],
            [sg.Col(column_layout, size=(1200, 796), scrollable=True)]]

    window = sg.Window('Table', layout, return_keyboard_events=True, resizable=True)

    while True:
        event, values = window.read(timeout=1000)

        # --- Process buttons --- #
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event in ("-Refresh-", sg.TIMEOUT_KEY):
            drafted = [f"{x['metadata']['first_name']} {x['metadata']['last_name']}" for x in draft.get_all_picks()]
            window["-Drafted-"].update(values=drafted)
            # for loop to set the drafted players as "clicked"
            for c in range(MAX_COL):
                for r in range(MAX_ROWS):
                    cur_player_name = window[(r, c)].get_text()
                    cur_player_name = cur_player_name.replace("\n", " ")
                    for players in drafted:

                        if players in cur_player_name:
                            window[(r, c)].metadata["is_clicked"] = True
                            window[(r, c)].update(button_color='white on gray')
                        else:
                            pass

        elif event == '-Search-':
            search_text = values["-Search-"].lower()
            for c in range(MAX_COL):
                for r in range(MAX_ROWS):
                    if search_text == "":
                        if window[(r, c)].metadata["is_clicked"]:
                            window[(r, c)].update(button_color='white on gray')
                        else:
                            window[(r, c)].update(button_color=BG_COLORS[db[r, c]["position"]])
                    elif search_text in window[(r, c)].get_text().lower():
                        window[(r, c)].update(button_color="black on yellow")
                    else:
                        if window[(r, c)].metadata["is_clicked"]:
                            window[(r, c)].update(button_color='white on gray')
                        else:
                            window[(r, c)].update(button_color=BG_COLORS[db[r, c]["position"]])



        elif event == '-Drafted-':
            pass
            """
            search_text = values["-Drafted-"].lower()
            for player in drafted_list:
                # pdb.set_trace()
                for c in range(MAX_COL):
                    for r in range(MAX_ROWS):
                        if player in window[(r, c)].get_text().lower():
                            window[(r, c)].update(button_color="gray")
                        else:
                            pdb.set_trace()
                        
                        button_reset_color = f"white on {BG_COLORS[db[r, c]['position']]}"
                        if search_text == "":
                            window[(r, c)].update(button_color=button_reset_color)
                        elif search_text in window[(r, c)].get_text().lower():
                            window[(r, c)].update(button_color="gray")
                        else:
                            window[(r, c)].update(button_color=button_reset_color)"""

        # click on button event
        elif event in [(r, c) for c in range(MAX_COL) for r in range(MAX_ROWS)]:
            r, c = event
            window[(r, c)].metadata["is_clicked"] = not window[(r, c)].metadata["is_clicked"]
            if window[(r, c)].metadata["is_clicked"]:
                window[(r, c)].update(button_color='white on gray')
            else:
                window[(r, c)].update(button_color=BG_COLORS[db[r, c]["position"]])
        elif event == "-Load-ADP-":
            db = np.array(adp_list)
            db = np.reshape(db, (16, 12))
            db[1::2, :] = db[1::2, ::-1]
            for c in range(MAX_COL):
                for r in range(MAX_ROWS):
                    window[(r, c)].update(
                        button_color=BG_COLORS[db[r, c]["position"]],
                        text=f"{db[r, c]['name'].split(' ', 1)[0]}\n"
                             f"{db[r, c]['name'].split(' ', 1)[1]}\n"
                             f"{db[r, c]['position']} ({db[r, c]['team']}) {db[r, c]['bye']}"
                    )
        elif event == "-Load-VBD-":
            db = np.array(vbd_list)
            db = np.reshape(db, (16, 12))
            db[1::2, :] = db[1::2, ::-1]
            for c in range(MAX_COL):
                for r in range(MAX_ROWS):
                    try:
                        window[(r, c)].update(
                            button_color=BG_COLORS[db[r, c]["position"]],
                            text=f"{db[r, c]['name'].split(' ', 1)[0]}\n"
                                 f"{db[r, c]['name'].split(' ', 1)[1]}\n"
                                 f"{db[r, c]['position']} ({db[r, c]['team']}) {db[r, c]['bye']}"
                        )
                    except KeyError:
                        window[(r, c)].update(
                            button_color=BG_COLORS[db[r, c]["position"]],
                            text=f"{db[r, c]['name'].split(' ', 1)[0]}\n"
                                 f"{db[r, c]['name'].split(' ', 1)[1]}\n"
                                 f"{db[r, c]['position']} ({db[r, c]['team']})"
                        )
                    except AttributeError:
                        pdb.set_trace()

        elif event == 'About...':
            sg.popup('Demo of table capabilities')
        elif event == 'Open':
            filename = sg.popup_get_file(
                'filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
            # --- populate table with file contents --- #
            if filename is not None:
                with open(filename, "r") as infile:
                    reader = csv.reader(infile)
                    try:
                        # read everything else into a list of rows
                        data = list(reader)
                    except:
                        sg.popup_error('Error reading file')
                        continue
                # clear the table
                [window[(i, j)].update('') for j in range(MAX_COL)
                 for i in range(MAX_ROWS)]

                for i, row in enumerate(data):
                    for j, item in enumerate(row):
                        location = (i, j)
                        try:  # try the best we can at reading and filling the table
                            target_element = window[location]
                            new_value = item
                            if target_element is not None and new_value != '':
                                target_element.update(new_value)
                        except:
                            pass

        elif event == "Set Keeper":

            # if a valid table location entered, change that location's value
            try:
                player_name = window['Keeper Combo'].get()
                # print(player_name)
                player_index = next((i for (i, d) in enumerate(adp_list) if d["name"] == player_name), None)
                keeper_dict = adp_list.pop(player_index)
                keeper_dict["keeper"] = True
                keeper_dict["keeper_location"] = (int(values['-Keeper Round-']-1), int(values['-Keeper Pick-']-1))
                adp_list.append(keeper_dict)
                db = np.array(adp_list)
                db = np.reshape(db, (16, 12))
                db[1::2, :] = db[1::2, ::-1]
                print(db)


                # location = (int(values['inputrow']), int(values['inputcol']))
                target_element = window[keeper_dict['keeper_location']]
                new_value = f"{keeper_dict['name'].split(' ', 1)[0]}\n"\
                            f"{keeper_dict['name'].split(' ', 1)[1]}\n"\
                            f"{keeper_dict['position']} ({keeper_dict['team']}) {keeper_dict['bye']}"
                if target_element is not None and new_value != '':
                    target_element.update(new_value)

            except:
                pass
    try:
        print(draft.get_all_picks())
        drafted_list = [f"{x['metadata']['first_name']} {x['metadata']['last_name']}" for x in draft.get_all_picks()]
        print(drafted_list[-1])
    except:
        pdb.set_trace()

    # window["-Drafted-"].update(values=drafted_list)
    window.close()


TableSimulation()
