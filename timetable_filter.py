from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror, askquestion, askretrycancel
import json
import os
import pickle


CHAR_TO_INT = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}


def parse_out_grups(timetable):
    possible_groups = dict()
    for hour in timetable:
        if (hour["przedmiot"], hour["typ"]) in possible_groups.keys():
            possible_groups[(hour["przedmiot"], hour["typ"])].add(hour["grupa"])
        else:
            possible_groups[(hour["przedmiot"], hour["typ"])] = {hour["grupa"]}
    for key in possible_groups.keys():
        possible_groups[key] = sorted(list(possible_groups[key]))
    subject_groups = dict()
    for hour in timetable:
        subject_groups[(hour["przedmiot"], hour["typ"])] = "unknown"
    for sub in subject_groups.keys():
        if len(possible_groups[sub]) > 1:
            while True:
                print(
                    "------------------------------------------------------------------------------------------------"
                )
                print(f"Possible groups for subject {sub[0]} {sub[1]}")
                list(
                    [
                        print(f" {i + 1}.  {g}")
                        for i, g in enumerate(possible_groups[sub])
                    ]
                )
                print(f"Select group index :")
                try:
                    subject_groups[sub] = possible_groups[sub][int(input()) - 1]
                    break
                except Exception:
                    if askretrycancel("Error", "Invalid group name index."):
                        exit()
        else:
            subject_groups[sub] = possible_groups[sub][0]

    return subject_groups


def filter_timetable(timetable, groups):
    return filter(
        lambda hour: (hour["przedmiot"], hour["typ"]) in groups.keys()
        and hour["grupa"] == groups[(hour["przedmiot"], hour["typ"])],
        timetable,
    )


def forge_html_table(timetable):
    """
    "dzien"
    "godz"
    "przedmiot"
    "grupa"
    "nauczyciel"
    "sala"
    "typ"
    "uwagi"
    "datado"
    """
    table_content = {}
    i0 = -1
    while i0 < len(timetable) - 1:
        i0 += 1
        # loop all next identical subject hours
        i1 = i0
        while i1 < len(timetable) - 1:
            i1 += 1
            if (
                timetable[i0]["przedmiot"] == timetable[i1]["przedmiot"]
                and timetable[i0]["typ"] == timetable[i1]["typ"]
                and timetable[i0]["dzien"] == timetable[i1]["dzien"]
                and timetable[i0]["grupa"] == timetable[i1]["grupa"]
            ):
                continue
            else:
                print(timetable[i0]["przedmiot"])
                break
        if not i1 < len(timetable) - 1:
            i1 += 1
        # number of repeated hours
        timetable[i0]["len"] = i1 - i0
        if timetable[i0]["dzien"] in table_content.keys():
            table_content[timetable[i0]["dzien"]].append(timetable[i0])
        else:
            table_content[timetable[i0]["dzien"]] = [timetable[i0]]
        i0 = i1 - 1

    # list for merged day timetables
    day_row = [
        """<div class="table_title">Poniedzia\u0142ek</div>""",
        """<div class="table_title">Wtorek</div>""",
        """<div class="table_title">\u015aroda</div>""",
        """<div class="table_title">Czwartek</div>""",
        """<div class="table_title">Pi\u0105tek</div>""",
    ]
    for i, day in enumerate(
        ["Poniedzia\u0142ek", "Wtorek", "\u015aroda", "Czwartek", "Pi\u0105tek"]
    ):
        if day in table_content.keys():
            for sub in table_content[day]:
                day_row[
                    i
                ] += f"""
                    <div class="hour{sub['godz'][:-3]} l{sub['len']} data_cell t_{sub['typ'].replace(".", "")}">
                        <div class="sub_title">
                        <div class="subject">{sub['przedmiot']}</div>
                        <div class="stype">{sub['typ']}</div>
                        </div>
                        <div class='room'>{f"s. {sub['sala']}" if sub['sala'] else "ONLINE"}</div>
                        <div class="adnotations">{sub['uwagi']}</div>
                    </div>
                """
    day_row.insert(
        0,
        "".join(
            [
                f"""<div class="data_cell l1 hour{i}">{i}.00</div>"""
                for i in range(8, 20)
            ]
        ),
    )

    style = "".join(
        [f".hour{i}" + "{top:" + str(5 * (i - 8) + 2) + "em;}" for i in range(8, 20)]
    ) + "".join([f".l{i}" + "{height:" + str(5 * i) + "em;}" for i in range(1, 6)])
    return f"""
        <!doctype html><html lang="pl"><head><meta charset="utf-8"><title>Filtered timetable</title>
        <meta name="description" content=""><meta name="author" content="KW">
        <link rel="stylesheet" href="timetable.css">
        <style>{style}</style></head><body>
        <div class="timetable">
        {"".join(f'<div class="column {"time_column" if not i else ""}">{day}</div>' for i, day in enumerate(day_row))}
        </div></body></html>
        """.encode(
        "utf-8"
    )


def main():
    root = Tk()
    root.overrideredirect(1)
    root.wm_attributes("-topmost", 1)
    root.withdraw()
    # tkinter askopenfilename dialog, return path
    filepath = askopenfilename()
    if not filepath:
        showerror("No file selected", "No file selected, application will exit now.")
        exit()
    # load json, catch decoding error if occurs and terminate
    try:
        with open(filepath, "r") as file:
            timetable = json.load(file)
    except json.JSONDecodeError:
        showerror(
            "Error",
            "We were unable to parse this file, make sure that it is a valid json file.",
        )
        return
    # if no groups mapping file found it needs to be created, then continue
    groups_file_path = os.path.splitext(filepath)[0] + "_groups.json"
    if os.path.exists(groups_file_path) and "yes" == askquestion(
        "Loading resource", "Do you want to load already created groups file?"
    ):
        with open(groups_file_path, "rb") as file:
            groups = pickle.load(file)
    else:
        try:
            groups = parse_out_grups(timetable)
            with open(groups_file_path, "wb") as file:
                pickle.dump(groups, file)
        except KeyError:
            showerror("Error", "Timetable seem to be malformed.")
            exit()
    print(
        "------------------------------------------------------------------------------------------------"
    )
    list(
        [
            print(f"- {sub[0]:_<50} {sub[1]: <5}  group:  {groups[sub]}")
            for sub in groups.keys()
        ]
    )
    timetable = list(filter_timetable(timetable, groups))
    with open(os.path.splitext(filepath)[0] + "_filtered.json", "w") as file:
        json.dump(timetable, file)

    with open(os.path.splitext(filepath)[0] + "_filtered.html", "wb") as file:
        file.write(forge_html_table(timetable))


if __name__ == "__main__":
    main()
