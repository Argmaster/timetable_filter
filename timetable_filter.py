from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror, askquestion
import json
import os
import pickle


def parse_out_grups(timetable):
    # *
    # first dictionary contains possible groups for each subject & type pair,
    # to be displayed for user while asking for group indexes
    # *
    possible_groups = dict()
    # *
    # List all subjects while looping for future usage
    # *
    subjects = set()
    for hour in timetable:
        # *
        # There are no repetitions in group options bcs they are stored in sets
        # *
        sub = (hour["przedmiot"], hour["typ"])
        subjects.add(sub)
        if sub in possible_groups.keys():
            possible_groups[sub].add(hour["grupa"])
        else:
            possible_groups[sub] = {hour["grupa"]}
    # *
    # convert sets to alphabetically sorted lists
    # *
    possible_groups = dict({sub: sorted(possible_groups[sub]) for sub in subjects})
    for sub in sorted(subjects, key=lambda x: x[1]):
        print(f"{sub[1]: <5} {sub[0]}")
    # *
    # (subject, type) => group_name
    # *
    subject_groups = dict()
    for sub in sorted(subjects, key=lambda x: x[0]):
        # *
        # If there are more than one option, ask user to decide which one to use
        # *
        if len(possible_groups[sub]) > 1:
            # *
            # Print out all possible choices, indexed
            # *
            print(
                "------------------------------------------------------------------------------------------------"
            )
            print(f"Possible groups for subject {sub[0]} {sub[1]}")
            list([print(f" {i + 1}.  {g}") for i, g in enumerate(possible_groups[sub])])
            print(f"Select group index :")
            # *
            # Infinite while loop allowing user to retry or exit in case of invalid input
            # If input is valid, loob is broken
            # *
            while True:
                try:
                    subject_groups[sub] = possible_groups[sub][int(input()) - 1]
                    break
                except Exception:
                    if "no" == askquestion("Error", "Invalid group name index, retry?"):
                        exit()
                    print("Retry:")
        else:
            # *
            # autocomplete if there is only one option
            # *
            subject_groups[sub] = possible_groups[sub][0]
    return subject_groups


def filter_timetable(timetable, groups):
    # *
    # ???
    # *
    return filter(
        lambda hour: (hour["przedmiot"], hour["typ"]) in groups.keys()
        and hour["grupa"] == groups[(hour["przedmiot"], hour["typ"])],
        timetable,
    )


def forge_html_table(timetable):
    # *
    # Dictionary will contain merged lesson hours
    # Where "len" key will contain length of block
    # with min val 1
    # *
    reduced_timetable = {}
    index_current = -1
    while index_current < len(timetable) - 1:
        index_current += 1
        # *
        # loop all next identical subject hours
        # *
        index_next = index_current
        while index_next < len(timetable) - 1:
            # *
            # Loop until some next lesson hour is not today or
            # different type/subject/group from current
            # *
            index_next += 1
            if (
                timetable[index_current]["przedmiot"]
                == timetable[index_next]["przedmiot"]
                and timetable[index_current]["typ"] == timetable[index_next]["typ"]
                and timetable[index_current]["dzien"] == timetable[index_next]["dzien"]
                and timetable[index_current]["grupa"] == timetable[index_next]["grupa"]
            ):
                continue
            else:
                break
        if not index_next < len(timetable) - 1:
            # *
            # After no longer looping through timetable is posible,
            # we need to increment index_next last time
            # *
            index_next += 1
        # *
        # subject length in hours
        # *
        timetable[index_current]["len"] = index_next - index_current
        # *
        # if yet no subject for this day, create list
        # for it, otherwise just append
        # *
        if timetable[index_current]["dzien"] in reduced_timetable.keys():
            reduced_timetable[timetable[index_current]["dzien"]].append(
                timetable[index_current]
            )
        else:
            reduced_timetable[timetable[index_current]["dzien"]] = [
                timetable[index_current]
            ]
        index_current = index_next - 1
    # *
    # List agregating all days in timetable, starts with day label cell
    # *
    day_row = [
        """<div class="table_title">Poniedzia\u0142ek</div>""",
        """<div class="table_title">Wtorek</div>""",
        """<div class="table_title">\u015aroda</div>""",
        """<div class="table_title">Czwartek</div>""",
        """<div class="table_title">Pi\u0105tek</div>""",
    ]
    # *
    # Week days have to be specified manually as i dont
    # really want to fetch them from timetable
    # *
    for i, day in enumerate(
        ["Poniedzia\u0142ek", "Wtorek", "\u015aroda", "Czwartek", "Pi\u0105tek"]
    ):
        if day in reduced_timetable.keys():
            # *
            # For each day, iteratre through all subjects
            # *
            for sub in reduced_timetable[day]:
                day_row[
                    i
                ] += f"""
                    <div class="hour{sub['godz'][:-3]} l{sub['len']} data-cell t_{sub['typ'].replace(".", "")}">
                        <div class="inner-cell">
                            <div class="sub-title">
                            <div class="subject">{sub['przedmiot']}</div>
                            <div class="stype">{sub['typ']}</div>
                            </div>
                            <div class='room'>{f"s. {sub['sala']}" if sub['sala'] else "ONLINE"}</div>
                            <div class="adnotations">{sub['uwagi']}</div>
                        </div>
                    </div>
                """
    # *
    # insert hour labels column at the beginging of each row
    # *
    day_row.insert(
        0,
        "".join(
            [
                f"""<div class="data-cell l1 hour{i}">
                    <div class="inner-cell">
                        {i}.00
                    </div>
                </div>"""
                for i in range(8, 20)
            ]
        ),
    )

    style = "".join(
        [f".hour{i}{{top: {5 * (i - 8) + 2}em;}}\n" for i in range(8, 20)]
    ) + "".join([f".l{i}{{height: {5 * i}em;}}\n" for i in range(1, 6)])
    try:
        with open("timetable.css", "r", encoding="utf-8") as file:
            style += file.read()
    except FileNotFoundError:
        if "no" == askquestion(
            "CSS file not found",
            "Program was unable to find file timetable.css, without task cannot be fully completed. Continue?",
        ):
            exit()
    return f"""
        <!doctype html>
        <html lang="pl">
            <head>
                <meta charset="utf-8">
                <title>Filtered timetable</title>
                <meta name="description" content="">
                <meta name="author" content="KW">
                <style>{style}</style>
                <link rel="stylesheet" href="timetable.css">
            </head><body>
            <div class="timetable">
            {"".join(f'<div class="column {"time_column" if not i else ""}">{day}</div>' for i, day in enumerate(day_row))}
            </div>
        </body></html>
        """.encode(
        "utf-8"
    )


def main():
    # *
    # Create invincible topmost Tkinter window for popups
    # *
    root = Tk()
    root.overrideredirect(1)
    root.wm_attributes("-topmost", 1)
    root.withdraw()
    # *
    # tkinter askopenfilename dialog, return path to json file
    # containing filetable to be filtered
    # *
    while True:
        filepath = askopenfilename(filetypes=[("JSON files", ".json")])
        # *
        # Without filepath program will terminate
        # *
        if not filepath:
            # *
            # Ask user if he want to retry
            # *
            if "no" == askquestion(
                "No file selected",
                "Program will exit if you wont select valid timetable file, retry?",
            ):
                exit()
        else:
            break
    filtered_timetable_path = os.path.splitext(filepath)[0] + "_filtered.json"
    # *
    # If there is already fiiltered file for selected timetable file
    # as if user is willing to use it or overwrite it creating new
    # *
    if os.path.exists(filtered_timetable_path) and "yes" == askquestion(
        "Loading resource",
        "Do you want to load already created filtered timetable file?",
    ):
        with open(filtered_timetable_path, "r") as file:
            filtered_timetable = json.load(file)
    else:
        try:
            # *
            # load json, selected json file
            # *
            with open(filepath, "r") as file:
                timetable = json.load(file)
        except json.JSONDecodeError:
            # *
            # in case of error program will simply terminate,
            # there is no point in creating huge loop now
            # to let user retry here
            # *
            showerror(
                "Error",
                "We were unable to parse this file, make sure that it is a valid json file.",
            )
            exit()
        # *
        # groups file contains pickled list of user subject groups
        # ("subject_name", "subject_type") => "group_name"
        # *
        groups_file_path = os.path.splitext(filepath)[0] + "_groups.pickle"
        # *
        # if no groups mapping file found it needs to be created
        # while file exists popup yes/no will appear asking if
        # user is willing to reuse already existing groups file
        # *
        if os.path.exists(groups_file_path) and "yes" == askquestion(
            "Loading resource", "Do you want to load already created groups file?"
        ):
            # *
            # dict(("subject_name", "subject_type") => "group_name")
            # *
            with open(groups_file_path, "rb") as file:
                groups = pickle.load(file)
        else:
            try:
                # *
                # Groups are selected base on timetable
                # *
                groups = parse_out_grups(timetable)
                # *
                # Saved in file, while opened second time
                # app will ask if user is willing to reuse already
                # created file
                # *
                with open(groups_file_path, "wb") as file:
                    pickle.dump(groups, file)
            except json.JSONDecodeError:
                # *
                # Program will terminate if there is key missing in timetable,
                # "dzien" "godz" "przedmiot" "grupa" "nauczyciel" "sala" "typ" "uwagi" "datado"
                # keys are expected and timetable is list of dicts
                # *
                showerror("Error", "Timetable seem to be malformed.")
                exit()
        # *
        # Print selected group for each (subject, type) combination
        # *
        print(
            "------------------------------------------------------------------------------------------------"
        )
        list(
            [
                print(f"- {sub[0]:_<50} {sub[1]: <5}  group:  {groups[sub]}")
                for sub in groups.keys()
            ]
        )
        # *
        # Filter out timetable data and save it *fname*_filtered.json file
        # *
        filtered_timetable = list(filter_timetable(timetable, groups))
        with open(filtered_timetable_path, "w") as file:
            json.dump(filtered_timetable, file)
    # *
    # Ask user if he wants to save filtered timetable as html
    # *
    if "yes" == askquestion(
        "Saving filtered timetable", "Do you want to save filtered timetable as html?"
    ):
        with open(os.path.splitext(filepath)[0] + "_filtered.html", "wb") as file:
            file.write(forge_html_table(filtered_timetable))


if __name__ == "__main__":
    main()
