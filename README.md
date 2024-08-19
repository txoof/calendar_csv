# Google Calendar CSV Generator

Python script for generating files suitable for import into Google Calendar based on a schedule files for N-day rotating block schedules. This script will produce one CSV for each unique event as well as a CSV for each day in the block rotation.

For example, if your rotating schedule has "Block A, Block B, Block C, Lunch, Break 1, Break 2" seven CSV files will be produced, one for each event in the rotation: e.g. Block A, Block B, Block C, lunch, breaks. Each file produced will contain all of the calendar events for all days that match that event.

See the [Sample CSV](./sample_csv/) directory in this repository for an example of an 8-day rotation with blocks A, B, C, D, E, F, G, H, Lunch, Flex Time and Breaks and several other events. This example is based on the [HS Bell Schedule](./bell_schedule_hs.csv) included.


## Table of Contents <!-- omit from toc -->

- [Google Calendar CSV Generator](#google-calendar-csv-generator)
  - [Common Patterns \& Use Case](#common-patterns--use-case)
  - [Getting Started](#getting-started)
  - [Use](#use)
  - [Import CSV Files into Google Calendar](#import-csv-files-into-google-calendar)
  - [Command Reference](#command-reference)
  - [Additional Tools](#additional-tools)

## Common Patterns & Use Case

Many schools use a rotating schedule with an alternate, shortened time-table that is used on one day. In the example shown below, the schedule begins with a "Day 1" on the first day of school and continues 8 school-days before starting again. Weekends and holidays are not counted, only days that are considered "instructional" are counted.

In the example below, Wednesdays have an altered schedule with shorter blocks and an earlier dismissal time. Any time a school day falls on a Wednesday, a shortened version of the schedule is used.

| Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 | Day 8 | Day 1 |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Weds: 21/08/17 | Thurs: 21/08/18 | Fri: 21/08/19 | Mon: 21/08/23 | Tues: 21/08/24 | Weds: 21/08/25 | Thurs: 21/08/26 | Fri: 21/08/27 | Mon: 21/08/30 |
| Alternate Sch. | Standard Sch. | Standard Sch. | Standard Sch. | Standard Sch. | Alternate Sch. | Standard Sch. | Standard Sch. | Standard Sch. |

The example [high schools](./bell_schedule_hs.csv) schedule has 8 instructional blocks (A..H), two breaks, a "Flex" block and Lunch. When run through this scrip, 14 CSV files will be produced, one for each instructional block, the flex, break and lunch blocks. Teachers can then import just the blocks that are relevant to their work (e.g. [A, B, D, F, H, Break 2, Flex] ). Additionally, a rotation_Day.csv is included. The rotation_day file includes "all day" events that indicate the rotation day as well as the N/Total school days.

To get started, check the HS or MS bell schedule files included in this repo and see the [Creating a CSV File](#creating-a-csv-file) below.

## Getting Started

### Novice Instructions <!-- omit from toc -->

1. [Download this Zip File](https://github.com/txoof/calendar_csv/archive/refs/heads/master.zip)
2. Unpack the zip file by double clicking on it in *Finder*
3. Create (or update) the following files. It is easiest if the file names do **not** have any spaces.
   - `bell_schedule.csv` - This file contains the bell schedule timing for each block (an example file is provided)
   - `non_instruction.txt` - This file contains the dates in YYYY/MM/DD format that are considered "non instructional" such as conference days or PD days. 
4. Run the *Terminal.app* application (found in the applications folder)
![Terminal](./Documentation/terminal.png)
1. Type `cd` followed by a space in the terminal window
2. Click on the unzipped folder in Finder and drag it into the terminal window. Then press `Enter` (`⏎` key).
   - This will add the "path" to the program so you don't need to type it
![drag folder](Documentation/drag_folder.gif)
1. Paste the following command into the terminal window and press enter. **NOTE:** you may need to change the file names and dates to match your files and dates before pressing `Enter` (`⏎` key).
   - `./gcal_csv_generator.py  --schedule_file ./school_schedule_file.csv
   --start "2022/08/17" --end "2023/06/16" --non_instruction ./non_instruction.txt --alternate_day Wednesday`
8. CSV files will appear on your desktop in a folder

## Use

You will need the following:

* Schedule file in [`.csv` format](./bell_schedule_hs.csv)
  * Blank lines are ignored
* Non-instructional days file 
  * [Flat file with one day per line in YYYY/MM/DD format](./non_instruction_sample.txt)
  * Days that the rotation should "skip" such as holidays, parent-teacher conferences, PD Days, etc. Weekend days (Saturday & Sunday) are automatically skipped
* First and Last date of the instructional term
  * `YYYY/MM/DD` format: `2022/08/29`

### Creating a Schedule file <!-- omit from toc -->

To create a CSV file, use the sample [CSV template](./bell_schedule_sample.csv) provided.

See the [HS Sample](./bell_schedule_hs.csvv) for a 8-Block rotation over 8 days with an alternate shortened schedule.

**Required Columns:**

- **`day`** Unique title of day in rotation (e.g. Day 1, Blue, Alpha, etc.)
- **`subject`** Title of subject/block name (e.g. Block A, 3A Music, Lunch, etc.)
- **`start`** Start time in HH:MM format (e.g. 13:55, 08:30)
- **`end`** End time in HH:MM format
- **`alternate`** this is an "alternate" schedule as boolean: (True/False/\<blank\>)
- Any additional columns will be ignored

#### Considerations When Creating a CSV Schedule File <!-- omit from toc -->

- Use consistent names for the `subject` column. Events will be grouped based on the names. For example all events called *A Block* will be grouped in one file for import into a google calendar. If the file contains *A Block* in some places and *Block A* in others, they will be treated as different events. BE CONSISTENT.
- Day names can be anything that suits your needs. Again, be consistent for sanity.


### Generate Calendar CSV Files <!-- omit from toc -->

Examples:

- Generate a calendar based on `school_schedule_file.csv`, for a school year that begins on 8 August, 2022 and ends on 16 June 2023 with an alternate timing schedule on Wednesdays.

```bash
./gcal_csv_generator.py  --schedule_file ./school_schedule_file.csv \
--start "2022/08/17" --end "2023/06/16" --non_instruction ./non_instruction.txt \
--alternate_day Wednesday
```

- Generate a calendar based on `school_schedule_file.csv`, for a school year that begins on 8 August, 2022 and ends on 16 June 2023 with an alternate timing schedule on Tuesdays with a week that begins on Sunday and ends on Thursday.

```bash
./gcal_csv_generator.py  --schedule_file ./school_schedule_file.csv \
--start "2022/08/17" --end "2023/06/16" --non_instruction ./non_instruction.txt \
--alternate_day Wednesday --week_start Sunday --week_end Friday
```

## Import CSV Files into Google Calendar

The CSV files meet the specifications for Google Calendar and can be easily imported. See [Google's Excelent instructions for importing Events](https://support.google.com/calendar/answer/37118?hl=en&co=GENIE.Platform%3DDesktop) for more information. Before continuing ***READ ALL OF THIS SECTION.***

Teachers that need to add *Block A* to their calendar import the *Block_A.csv* file into their google calendar with no modifications. It is possible to modify the CSV file to make events easier to read in Google Calendar. See [Modifying CSV Files](#modifying-csv-files) below.

### IMPORTANT WARNING <!-- omit from toc -->

Google makes it very easy to import events, but there is **absolutely no way to undo an import**. Imported events must be manually deleted ONE-BY-ONE. It is prudent to create a "test calendar" and import your events for verification before commiting them to your personal calendar. **YOU HAVE BEEN WARNED.**

### Modifying CSV Files <!-- omit from toc -->

By default, the CSV will add events to the calendar using the `subject` line provided in the schedule file. This will typically look something like "Block B" or "Flex Time" or "AM Break".

To make the events easier to read in your calendar, open the csv in Google Sheets, Excel, vim or your favorite stream editor and find/replace the subject with a title of your choice.

For example, if you teach "Great Authors: Homer" in Block B, and want "Great Authors: Homer" to appear on your calendar, do the following:

1. Obtain a copy of the "Block_B.csv" file
2. Open the file in your favorite editor (e.g. Google Sheets)
3. Click: Edit > Find and Replace
4. In the Find and Replace dialogue find "Block B" and replace with "Great Authors: Homer"
5. Export the file as a CSV and import into Google Calendar


Here's a nice one-liner to do a find and replace with sed:
```bash
$ cat Block_B.csv | sed 's/Block B/Great Authors: Homer/g' > great_authors.csv
```

## Command Reference

```text
Usage: gcal_csv_generator.py [-h] --schedule_file /schedule/file.csv --start "YYYY/MM/DD" --end "YYYY/MM/DD" --non_instruction /path/to/non_instruction.txt [--date_format "%Y/%m/%d"] [--alternate_day Wednesday] [--output /output/location/] [--week_start Monday-Sunday] [--week_end Monday-Sunday]

options:
  -h, --help            show this help message and exit

  --schedule_file /schedule/file.csv, -c /schedule/file.csv
                        file containing CSV schedule data

  --start "YYYY/MM/DD", -s "YYYY/MM/DD"
                        First day of classes in YYYY/MM/DD format

  --end "YYYY/MM/DD", -e "YYYY/MM/DD"
                        Last day of classes in YYYY/MM/DD format

  --non_instruction /path/to/non_instruction.txt, -n /path/to/non_instruction.txt
                        File containing non-instructional days between start and end date, one per line matching the daytime format
                        (YYYY/MM/DD)

  --date_format "%Y/%m/%d", -d "%Y/%m/%d"
                        datetime format see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

  --alternate_day Wednesday, -a Wednesday
                        single day to use "alternate" schedule specified in the schedule file

  --output /output/location/, -o /output/location/
                        Folder to use for output of CSV Schedules (default is ~/Desktop)

  --week_start Monday-Sunday
                        First day of a typical school week (e.g. Monday). Default: Monday

  --week_end Monday-Sunday
                        Last day of a typical school week (e.g. Friday). Default: Friday
```

## Additional Tools

Included in this repo is a script that will combine multiple CSV files into a single CSV to simplify uploading to Google Calendar. Try `./combine.sh` for usage information.