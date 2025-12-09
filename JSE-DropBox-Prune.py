#!/usr/bin/env python3

# + ------------------------------------------------------------------------------------- +
# | JSE DropBox Prune v1.0 - J. Scott Elblein                                             |
# + ------------------------------------------------------------------------------------- +
# |                                                                                       |
# | DESC                                                                                  |
# | Keep DropBox/Local directories pruned by matching file names via RegEx and keeping    |
# | only the X number of latest ones. Supports ignore-list as well.                       |
# |                                                                                       |
# | NOTES                                                                                 |
# | Great for running on a schedule to keep your DropBox from getting filled up when      |
# | for example keeping nightly database backups sent there.                              |
# |                                                                                       |
# | See repo ReadMe for any more info.                                                    |
# |                                                                                       |
# | REQ                                                                                   |
# | Uses the official DropBox API: pip install dropbox                                    |
# |                                                                                       |
# | REF                                                                                   |
# | https://chatgpt.com/share/691a76e7-6bd0-8010-91e8-2cc05abf4324                        |
# |                                                                                       |
# | TODO                                                                                  |
# |   (Opt) Could beef up the function by validating file sizes are a minimum size        |
# |        before deleting?                                                               |
# |                                                                                       |
# + ------------------------------------------------------------------------------------- +

# region IMPORTS ---------------------------------------------------------------------------------------------------- +

import argparse, datetime, dropbox, re, time, tomllib

from dropbox.exceptions import ApiError
from dropbox.files import FileMetadata
from pathlib import Path

# endregion

# region WORKING VARS ----------------------------------------------------------------------------------------------- +

# Cline args
parser = argparse.ArgumentParser()
parser.add_argument("--configPath", required=True, help="Path to your config .toml")
args = parser.parse_args()

# For stats when script completes
statsPer = []
statsTotal = {"processed": 0,
              "kept": 0,
              "deleted": 0,
              "ignored": 0,
              "kept_total_size": 0,
              "deleted_total_size": 0,
              "ignored_total_size": 0}

# endregion

# region CONFIG VARS ------------------------------------------------------------------------------------------------ +

# Read the config file
with open(args.configPath, "rb") as conf:
    config = tomllib.load(conf)

# Connect to DropBox
DBX = dropbox.Dropbox(
    app_key=config["settings"]["app_key"],
    app_secret=config["settings"]["app_secret"],
    oauth2_refresh_token=config["settings"]["refresh_token"]
)

# File pattern to search with
PATTERN = re.compile(config["settings"]["regex_pattern"], re.IGNORECASE | re.X)

# endregion

# region FUNCTIONS -------------------------------------------------------------------------------------------------- +

def time_pretty(seconds):
    """ Takes seconds and turns them into a more human-readable hh:mm:ss.ms """

    return str(datetime.timedelta(seconds=seconds))

def bytes_pretty(num_bytes, precision=2):
    """Return a human-readable byte size without useless trailing zeros."""

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    idx = 0

    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1

    # Format, strip trailing zeros and dot
    text = f"{size:.{precision}f}".rstrip("0").rstrip(".")
    return f"{text} {units[idx]}"

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    if config["settings"]["enable_logging"] and config["settings"]["log_file"]:
        with open(config["settings"]["log_file"], "a", encoding="utf-8") as logfile:
            logfile.write(line + "\n")

def walk_config(c):
    """Loops through the paths in the config hunting for sub-dicts containing individual path configs."""

    for key, value in c.items():
        if isinstance(value, dict):
            # If this dict represents a repo (has the fields we expect)
            if "path_dropbox" in value:
                do_prune(value)
            else:
                walk_config(value)

def do_prune(path_conf):
    """Delete all files in a Dropbox or Local folder that match PATTERN, except for the N most recent."""

    tmrStart = time.perf_counter()
    matched = []
    matched_ignored = 0
    stats = {"kept_size": 0, "deleted_size": 0, "ignored_size": 0} # Keeps only stats for this fn

    # Bail out if the local path is bad and user has chosen to prune local dirs
    if config["settings"]["local"] and not Path(path_conf["path_local"]).exists():
        log(f"{path_conf["name"]}: Nope, that path ain't real. Moving on. ({path_conf["path_local"]})")
        return

    # Tries fetching per path object 'keep', if nothing there, default to the global 'keep' in the config.
    # If for some reason user fucked both of those up, to keep the script from exploding, default to 1.
    keep = path_conf.get("keep") or config["settings"].get("default_keep") or 1

    # Let's go
    try:
        log(f"Scanning "
            f"{"DropBox" if not config["settings"]["local"] else "Local"} "
            f"{path_conf["name"]} "
            f"folder: {path_conf["path_dropbox"] if not config["settings"]["local"] else path_conf["path_local"]}")

        # Step 1: Collect matching files
        if not config["settings"]["local"]:
            # DBox
            result = DBX.files_list_folder(path_conf["path_dropbox"])
        else:
            # Local
            fol = Path(path_conf["path_local"])
            result = [f for f in fol.iterdir() if f.is_file()]

        # Loop through files in the path for any that match the RegEx user provided,
        # as well as any that user added to their ignore list.
        def collect(entries):
            nonlocal matched_ignored
            for entry in entries:
                if isinstance(entry, FileMetadata) or config["settings"]["local"]:
                    if PATTERN.search(entry.name):
                        if entry.name in path_conf["ignore"]:
                            # Count it as "matched but ignored"
                            matched_ignored += 1
                            stats['ignored_size'] += entry.size
                            statsTotal['ignored_total_size'] += entry.size
                            log(f"[IGNORED]: {entry.name} {bytes_pretty(entry.size)}")
                        else:
                            matched.append(entry)

        collect(result.entries if not config["settings"]["local"] else result)

        if stats['ignored_size']:
            log(f"  Total: {bytes_pretty(stats['ignored_size'])}")

        # If doing Dbox, keep going through the pagination until there are no more pages
        if not config["settings"]["local"]:
            while result.has_more:
                result = DBX.files_list_folder_continue(result.cursor)
                collect(result.entries)

        if not matched:
            log("No matching files found")
            return

        # Step 2: Sort by server_modified (for Dbox) or last_modified (local) desc (newest first)
        keyfunc = (lambda lm: lm.server_modified) if not config["settings"]["local"] else (lambda lm: lm.stat().st_mtime)
        matched.sort(key=keyfunc, reverse=True)

        # Step 3: Determine kept and deleted files
        statsTotal["processed"] += len(matched) + matched_ignored
        to_keep = matched[:keep]
        to_delete = matched[keep:]

        statsTotal["kept"] += len(to_keep)
        log(f"[KEEPING] ({len(to_keep)}) newest files:")
        for f in to_keep:
            mod = f.server_modified if not config["settings"]["local"] else f.stat().st_mtime
            stats['kept_size'] += f.size
            statsTotal['kept_total_size'] += f.size
            log(f"  KEEP: {f.name} {bytes_pretty(f.size)} (modified {mod})")

        log(f"  Total: {bytes_pretty(stats['kept_size'])}")

        # If we don't have anything new to delete, no sense in going through all this, eh?
        if to_delete:

            if config["settings"]["dry_run"]:
                log(f"[DRY RUN] no deletions will occur")
                log(f"Files that WOULD be deleted ({len(to_delete)}):")
                statsTotal["deleted"] += len(to_delete)
            else:
                log(f"[DELETING] ({len(to_delete)}) files:")

            # Step 4: Delete (or simulate)
            for d in to_delete:
                stats['deleted_size'] += d.size
                statsTotal['deleted_total_size'] += d.size
                log(f"  DELETE: {d.name} {bytes_pretty(d.size)}")
                if not config["settings"]["dry_run"]:
                    DBX.files_delete_v2(d.path_lower) if not config["settings"]["local"] else Path(d).unlink()

            log(f"  Total: {bytes_pretty(stats['deleted_size'])}")

        tmrEnd = time.perf_counter()
        log(f"Done pruning {path_conf["name"]}. Elapsed: {time_pretty(tmrEnd - tmrStart)}\n")

        # Final stats
        statsTotal['ignored'] += matched_ignored
        statsPer.append(f"Name: {path_conf['name']} | "
                        f"Processed: {len(matched) + matched_ignored} ({bytes_pretty(stats['kept_size'] + stats['deleted_size'] + stats["ignored_size"])}) | "
                        f"Kept: {len(to_keep)} ({bytes_pretty(stats['kept_size'])}) | "
                        f"Deleted: {len(to_delete)} ({bytes_pretty(stats['deleted_size'])}) | "
                        f"Ignored: {matched_ignored}{f' ({bytes_pretty(stats["ignored_size"])})' if stats['ignored_size'] else ''}")

    except ApiError as e:
        # Dbox API exception
        log(f"API error: {e}")

# endregion

if __name__ == "__main__":

    tmrTotalStart = time.perf_counter()

    walk_config(config["paths"])

    tmrTotalEnd = time.perf_counter()

    # Let's check if we have any per path stats to show first; we SHOULD, but if shit happens we might not,
    # so let's be thorough. If we don't then that report won't be shown.
    per_path_block = ""
    if statsPer:  # list has items
        per_path_block = (
            "TOTALS PER PATH\n"
            + "\n".join(statsPer)
        )

    log(
        f"{'[DRY RUN] ' if config['settings']['dry_run'] else ''}"
        f"{'DropBox' if not config['settings']['local'] else 'Local'} Pruning Complete!\n\n"
        f"Total Elapsed Time: {time_pretty(tmrTotalEnd - tmrTotalStart)}\n\n"
        f"TOTALS OVERALL\n"
        f"Processed: {statsTotal['processed']} ({bytes_pretty(statsTotal['kept_total_size'] + statsTotal['deleted_total_size'])}) | "
        f"Kept: {statsTotal['kept']} ({bytes_pretty(statsTotal['kept_total_size'])}) | "
        f"Deleted: {statsTotal['deleted']} ({bytes_pretty(statsTotal['deleted_total_size'])}) | "
        f"Matched Ignored: {statsTotal['ignored']}{f' ({bytes_pretty(statsTotal['ignored_total_size'])})' if statsTotal['ignored_total_size'] else ''}\n\n"
        f"{per_path_block}"
    )
