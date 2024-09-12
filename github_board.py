import argparse
import datetime
import json
import time
import pygit2

STEP = 86400  # seconds in a day
UTC_TO_PST_OFFSET = 28800  # seconds in 8 hours
COMMIT_MULTIPLIER = 1

def board_origin(today):
    last_cell_dt = today
    first_cell_dt = datetime.date(last_cell_dt.year - 1, last_cell_dt.month, last_cell_dt.day)
    first_cell_ux = time.mktime(first_cell_dt.timetuple()) - time.timezone + UTC_TO_PST_OFFSET
    return int(first_cell_ux) + sunday_offset(first_cell_dt)

def sunday_offset(date, reverse=False):
    if not reverse:
        offset = (7 - (datetime.date.weekday(date) + 1) % 7) * STEP
    else:
        offset = -((datetime.date.weekday(date) + 2) % 7) * STEP
    return offset

def template_to_tape(template, origin):
    tape = []
    (i, j) = (0, 0)
    for row in template:
        for col in row:
            if col > 0:
                tape.extend([origin + (i * 7 + j) * STEP] * col)
            i += 1
        i, j = 0, j + 1
    return tape

def load_template(file_path):
    template = []
    with open(file_path, "r") as f:
        l = []
        for c in f.read():
            if c.isdigit():
                l.append(int(c) * COMMIT_MULTIPLIER)
            elif c == "\n" and l:
                template.append(l)
                l = []
        if l:
            template.append(l)
    return template

def align_template(template, alignment=None):
    size = {
        "width": max([len(row) for row in template]) if len(template) > 0 else 0,
        "height": len(template),
    }
    board = {
        "width": 51,
        "height": 7,
    }
    out = template[:]

    if alignment == "center":
        offset = {
            "width": int((board["width"] - size["width"]) / 2),
            "height": int((board["height"] - size["height"]) / 2),
        }
        for i in out:
            i[0:0] = [0] * offset["width"]
        for i in range(offset["height"]):
            out.insert(0, [0])
        return out
    else:
        return out

def main(*args):
    email, repo_path, tpl_file, alignment = args
    tpl = load_template(tpl_file)
    tpl = align_template(tpl, alignment)

    repo = pygit2.init_repository(repo_path)
    if email is None:
        if "user.email" in repo.config:
            email = repo.config["user.email"]
        else:
            raise RuntimeError("Specify email (--email or -e).")
    tree = repo.TreeBuilder().write()
    parents = [] if repo.is_empty else [str(repo.head.target)]
    for timestamp in template_to_tape(tpl, board_origin(datetime.date.today())):
        author = pygit2.Signature(name="Anonymous", email=email, time=timestamp)
        commit = repo.create_commit("refs/heads/master", author, author, "", tree, parents)
        parents = [str(commit)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub board")
    parser.add_argument("-r", "--repo", required=True, help="Path to your git repository")
    parser.add_argument("-e", "--email", help="Your GitHub email")
    parser.add_argument("-t", "--template", required=True, help="Path to the template file")
    parser.add_argument("-a", "--alignment", help="Template alignment, options: center")
    args = parser.parse_args()
    main(args.email, args.repo, args.template, args.alignment)
