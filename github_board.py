import argparse
import datetime
import pygit2

STEP = 86400  # seconds in a day (24 hours * 60 minutes * 60 seconds)
COMMIT_MULTIPLIER = 1  # We can modify this if needed

def board_origin(today):
    """
    Calculate the start point for commits from exactly one year ago.
    """
    one_year_ago = today - datetime.timedelta(weeks=52)

    # Find the Sunday closest to one year ago
    while one_year_ago.weekday() != 6:  # 6 is Sunday
        one_year_ago -= datetime.timedelta(days=1)  # Move backward to the last Sunday
    
    return one_year_ago


def template_to_tape(template, origin):
    """
    Convert the template to a list of timestamps for commits over 52 weeks.
    """
    tape = []
    current_date = origin
    for week_offset in range(len(template[0])):  # Iterate over the columns (weeks)
        for day_offset, row in enumerate(template):  # Iterate over the rows (days)
            if row[week_offset] > 0:
                commit_time = current_date + datetime.timedelta(days=day_offset + week_offset * 7)
                tape.extend([commit_time] * row[week_offset])  # Repeat based on number of commits (row[week_offset])
    return tape


def load_template(file_path):
    """
    Load the template from the file.
    """
    template = []
    with open(file_path, "r") as f:
        for line in f:
            template.append([int(c) for c in line.strip() if c.isdigit()])
    return template


def main(email, repo_path, template_file, alignment):
    """
    Main function to generate GitHub commits based on the template.
    """
    template = load_template(template_file)
    repo = pygit2.init_repository(repo_path)

    if email is None:
        if "user.email" in repo.config:
            email = repo.config["user.email"]
        else:
            raise RuntimeError("You must specify an email or configure it in git.")

    tree = repo.TreeBuilder().write()

    today = datetime.date.today()
    origin = board_origin(today)  # Calculate the correct starting point (one year ago)

    # Generate the commit times based on the template
    commit_times = template_to_tape(template, origin)

    parents = [] if repo.is_empty else [str(repo.head.target)]

    for commit_time in commit_times:
        # Convert the datetime object to a UNIX timestamp
        author = pygit2.Signature(name="Anonymous", email=email, time=int(commit_time.strftime('%s')))
        commit = repo.create_commit("refs/heads/main", author, author, "", tree, parents)
        parents = [str(commit)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate GitHub commits based on a template.")
    parser.add_argument("-r", "--repo", required=True, help="Path to your git repository")
    parser.add_argument("-e", "--email", help="Your GitHub email")
    parser.add_argument("-t", "--template", required=True, help="Path to the template file")
    parser.add_argument("-a", "--alignment", help="Template alignment (e.g., center)")
    
    args = parser.parse_args()
    main(args.email, args.repo, args.template, args.alignment)


