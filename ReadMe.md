# JSE DropBox Prune

Keep DropBox/Local directories pruned by matching file names via RegEx and keeping only the X number of latest ones.

Supports ignore-list as well.

Great for running on a schedule to keep your DropBox from getting filled up when for example keeping nightly database backups sent there.

Uses the official DropBox API: `pip install dropbox`

### Backstory

I wrote this for myself because I have a (excellent!) script running on a server that creates nightly database backups of many of my sites, and ships them over to my DropBox account for storage.
The script doesn't have the innate ability to keep only x number of the latest backups on DropBox, and delete the rest in order to prevent my DropBox from filling up.
Thus, I'm frequently forced to manually do this annoying, mind-numbing minutae. (_I'm looking square at you,_ [PHPBU](https://github.com/sebastianfeldmann/phpbu). :p)

Hence this script's birth.

I've also never done any Python coding and wanted to feel it out, so this was the perfect excuse to dip my toes in the Python waters.

### Usage

The script runs off of a config file, so you edit the config file to your liking, and then call the script with the config file as an argument:

`python JSE-DropBox-Prune.py --configPath "JSE-DropBox-Prune.toml"`

Using config files allows for creating as many of them as wanted for different uses, such as different DropBox accounts, different paths to keep pruned, etc., you just pass the different config(s) as necessary.

See the sample config `JSE-DropBox-Prune-Sample.toml` for more info and how to config it.

It also keeps a .log of all actions performed.

### How?

My db backup script always names the files consistently; only the name of the site and timestamp change, so it uses a simple RegEx to match those files.

All matched files get added to the list of files to check and prune. Pretty simple.

You just edit the config to tell it how many of the latest files you want to keep, and it'll delete the rest.

A "dry run" is an option, and recommended to use at first until you have your RegEx tweaked perfectly how you want it. The dry run won't delete anything, it'll just show you in a log/on screen what WOULD have been kept/ignored/deleted.

After you've got it all set how you want it, just add it to a cronjob, Windows Task, what-have-you.
Of course, with a little imagination this script could be played with to do all kinds of different things for different purposes.

Btw, these sites are great for working out our RegEx: [RegEx101](https://regex101.com/) and [RegExr](https://regexr.com/)

**Note**

DropBox loves to mess with developers and constantly throw a wrench in the works, killing all our scripts with breaking changes, and force us all to waste time fixing them to get them back on track.
So in the case of the DropBox portion of this script breaking, as long as you have their official app installed on the same computer and its set to sync those files you can just use the "local path" option to keep them pruned, and the app itself will keep everything synced remotely. You can do that anyway if you prefer, and it's actually faster that way.

### Example Output

_Only showing 1 path output being pruned so as not to spam you here (others were cut out); you can add as many as you want to run at a single time as you need._

    [2025-12-05 22:00:01] Scanning DropBox GeekDrop folder: /Backups/Databases/a1/GeekDrop
    [2025-12-05 22:00:01] Ignored: geekdrop-2024-01-14-0257.sql.bz2.enc 46.16 MB
    [2025-12-05 22:00:01]   Total: 46.16 MB
    [2025-12-05 22:00:01] Keeping (2) newest files:
    [2025-12-05 22:00:01]   KEEP: geekdrop-2025-12-05-0000.sql.bz2.enc 68.79 MB (modified 2025-12-05 05:01:41)
    [2025-12-05 22:00:01]   KEEP: geekdrop-2025-12-04-0000.sql.bz2.enc 68.26 MB (modified 2025-12-04 05:01:48)
    [2025-12-05 22:00:01]   Total: 137.05 MB
    [2025-12-05 22:00:01] Deleting (20) files:
    [2025-12-05 22:00:01]   DELETE: geekdrop-2025-12-03-0000.sql.bz2.enc 69.44 MB
    [2025-12-05 22:00:02]   DELETE: geekdrop-2025-12-02-0000.sql.bz2.enc 71.67 MB
    [2025-12-05 22:00:02]   DELETE: geekdrop-2025-12-01-0000.sql.bz2.enc 68.66 MB
    [2025-12-05 22:00:03]   DELETE: geekdrop-2025-11-30-0000.sql.bz2.enc 71.85 MB
    [2025-12-05 22:00:03]   DELETE: geekdrop-2025-11-29-0000.sql.bz2.enc 70.42 MB
    [2025-12-05 22:00:04]   DELETE: geekdrop-2025-11-28-0000.sql.bz2.enc 76.17 MB
    [2025-12-05 22:00:04]   DELETE: geekdrop-2025-11-27-0000.sql.bz2.enc 74.27 MB
    [2025-12-05 22:00:05]   DELETE: geekdrop-2025-11-26-0000.sql.bz2.enc 75.73 MB
    [2025-12-05 22:00:05]   DELETE: geekdrop-2025-11-25-0000.sql.bz2.enc 84.44 MB
    [2025-12-05 22:00:05]   DELETE: geekdrop-2025-11-24-0000.sql.bz2.enc 76.81 MB
    [2025-12-05 22:00:06]   DELETE: geekdrop-2025-11-23-0000.sql.bz2.enc 77.19 MB
    [2025-12-05 22:00:06]   DELETE: geekdrop-2025-11-22-0000.sql.bz2.enc 78.86 MB
    [2025-12-05 22:00:07]   DELETE: geekdrop-2025-11-21-0000.sql.bz2.enc 80.6 MB
    [2025-12-05 22:00:07]   DELETE: geekdrop-2025-11-20-0000.sql.bz2.enc 80.97 MB
    [2025-12-05 22:00:09]   DELETE: geekdrop-2025-11-19-0000.sql.bz2.enc 87.02 MB
    [2025-12-05 22:00:09]   DELETE: geekdrop-2025-11-18-0000.sql.bz2.enc 599.97 MB
    [2025-12-05 22:00:09]   DELETE: geekdrop-2025-11-17-0000.sql.bz2.enc 488.96 MB
    [2025-12-05 22:00:10]   DELETE: geekdrop-2025-11-16-0000.sql.bz2.enc 329.74 MB
    [2025-12-05 22:00:10]   DELETE: geekdrop-2025-11-15-0000.sql.bz2.enc 86.91 MB
    [2025-12-05 22:00:11]   DELETE: geekdrop-2025-11-12-0000.sql.bz2.enc 77.47 MB
    [2025-12-05 22:00:11]   Total: 2.66 GB
    [2025-12-05 22:00:11] Done pruning GeekDrop. Elapsed: 0:00:10.008764
    
    [2025-12-05 22:02:02] DropBox Pruning Complete!
    
    Total Elapsed Time: 0:02:11.141271
    
    TOTALS OVERALL
    Processed: 304 (6.8 GB) | Kept: 15 (309.26 MB) | Deleted: 0 (6.5 GB) | Matched Ignored: 2 (49.83 MB)
    
    TOTALS PER PATH
    Name: GeekDrop | Processed: 23 (2.84 GB) | Kept: 2 (137.05 MB) | Deleted: 20 (2.66 GB) | Ignored: 1 (46.16 MB)

### Windows Task

You can run it in a Windows Task (just for example) like this:

Program:

`"D:\Coding\Program Files\Python\Python314\python.exe"`

Arguments:

`"C:\Scott\JSE-DropBox-Prune\JSE-DropBox-Prune.py" --configPath "C:\Scott\JSE-DropBox-Prune\MyConfigs\JSE-DropBox-Prune.toml"`

Start In:

`C:\Scott\JSE-DropBox-Prune`
