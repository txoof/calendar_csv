#!/usr/bin/env python3
# coding: utf-8






from pathlib import Path
import json
import csv
import sys
import argparse
import unicodedata
import re

# from dateutil import rrule
from datetime import datetime, timedelta






def do_exit(msg=None, value=0):
    if value > 0:
        print('EXIT DUE TO ERROR:')
    else:
        print('DONE')
    if msg:
        print(f'\t{msg}')
    
    sys.exit(0)






CSV_HEADERS = ['DAY', 'SUBJECT', 'START', 'END', 'ALTERNATE']
WEEKDAYS = {
    'MONDAY': 0,
    'TUESDAY': 1,
    'WEDNESDAY': 2,
    'THURSDAY': 3,
    'FRIDAY': 4,
    'SATURDAY': 5,
    'SUNDAY': 6
}






def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', '_', value).strip('-_')






def csv_to_json(csv_file, output_file=None):
    '''convert csv_file schedule to JSON
    
    Outputs a JSON compliant file with the same name as the input file
    at the specified location
    
    csv_format:
    DAY, SUBJECT, START, END, ALTERNATE
    Day 1, Block A, 12:05, 14:25, FALSE
    Day 1, Block A, 11:45, 12:55, TRUE
    
    Args:
        csv_file(`str`): path to input file
        output_path(`str`): path to output file
    
    Returns:
        str: full path to output file
    '''
    calendar_csv_file = Path(csv_file).expanduser().resolve()
    if output_file:
        calendar_json_file = Path(output_file).expanduser().resolve()
    else:
        calendar_json_file = Path(f'{calendar_csv_file.parent}/{calendar_csv_file.stem}.json')
    
    calendar_list = []
    try:
        with open(calendar_csv_file, 'r') as csvfile:
            for line in csv.DictReader(csvfile):
                calendar_list.append(line)
    except OSError as e:
        do_exit(f'Could not open csv file due to error: {e}', 1)
        

    # sanitize keys into upper case
    calendar_list_temp = []
    for event in calendar_list:
        temp_dict = {}
        for key, value in event.items():
            temp_dict[str(key).upper()] = value
        calendar_list_temp.append(temp_dict)
    calendar_list = calendar_list_temp
    
    # check for missing headers
    missing_headers = []
    for key in CSV_HEADERS:
#         if key in f[0].keys():
        if key in calendar_list[0].keys():
            pass
        else:
            missing_headers.append(key)
        
    if len(missing_headers) > 0:
        do_exit(f'{calendar_csv_file} is missing headers: {missing_headers}', 1)

    # get a set of unique days
    days_set = set()
    for event in calendar_list:
        days_set.add(event['DAY'])

    # build an empty JSON structure for standard & alternate-day calendars
    calendar_json_dict = {'STANDARD': {}, 'ALTERNATE': {}}
    for key in calendar_json_dict:
        for day in sorted(days_set):
            calendar_json_dict[key][day] = []

    # populate calendar with events
    for event in calendar_list:
        if not event['SUBJECT']:
            continue

        cal_type = 'STANDARD'
        try:
            if event['ALTERNATE'].lower() == 'true':
                cal_type = 'ALTERNATE'
        except AttributeError:
            pass
        calendar_json_dict[cal_type][event['DAY']].append(event)
        
    try:
        calendar_json_file.parent.mkdir(exist_ok=True)
    except OSError as e:
        do_exit(f'cannot write JSON output file at location: {calendar_json_file.parent}: {e}', 1)
   
    try:
        with open(calendar_json_file, 'w') as json_out:
            json.dump(calendar_json_dict, json_out, indent=3)
    except OSError as e:
        do_exit(f'cannot write JSON output file at location: {calendar_json_file.parent}: {e}', 1)
    return calendar_json_file






def read_non_instruction(file, dt_format):
    '''read flat text file containing non-instructional days
    
    Args:
        file(`str`): full path to file
        dt_format(`str`): daytime format of dates stored in file e.g. %Y/%d/%m
        
    Returns:
        list of daytime objects '''
    
    errors = []
    non_instruction_dt = []
    try:
        with open(file, 'r') as open_file:
            file_txt = open_file.readlines() 
    except OSError as e:
        do_exit(f'error opening file: {file}; {e}', 1)
        
    for idx, val in enumerate(file_txt):
        try:
            non_instruction_dt.append(datetime.strptime(val.strip(), dt_format))
        except ValueError as e:
            if val.isspace():
                pass
            else:
                errors.append((idx, val))
                
    if errors:
        print(f'Non-Instructional Days file "{file}" contains unknown date formats.')
        print(f'each line should contain only the date in the specified format.')
        print(f'default format: YYYY/MM/DD e.g. 2022/08/28')
        print(f'Current expected date format: {dt_format}')
        print('='*40)
        for each in errors:
            print(f'\tline: {each[0]+1} -> "{each[1].rstrip()}"')
        print('='*40)
        do_exit(f'unexpected date formats in "{file}".', 1)
        
    return non_instruction_dt






def read_json_schedule(file):
    '''read json formatted schedule file
    
    Args:
        file('str'): path to file
        
        
    Returns:
        `dict`'''
    
    try:
        with open(file, 'r') as json_file:
            json_data = json.load(json_file)
    except Exception as e:
        do_exit(f'failed to read json file "{file}": {e}', 1)
        
    return json_data






def set_school_days(start, end, non_instruction, dt_format):
    '''create a list of school days excluding non-instructional and weekends
    
    Args:
        start(`str`): first day of school in dt_format (e.g. YYYY/MM/DD)
        end(`str`): last day of school in dt_format
        non_instruction(`list` of `datetime`): non-instructional days
        dt_format(`str`): datetime format string (e.g. %Y/%m/%d)
        
    Returns:
        `list`'''
    
    start_dt = datetime.strptime(start, dt_format)
    end_dt = datetime.strptime(end, dt_format)
    
    delta = end_dt - start_dt
    
    all_days = [start_dt + timedelta(days=i) for i in range(delta.days + 1)]
    
    school_days = []
#     for dt in rrule.rrule(rrule.DAILY, dtstart=start_dt, until=end_dt):
    for dt in all_days:
        if dt not in non_instruction and datetime.weekday(dt) in range(0, 5):
            school_days.append(dt)
    return school_days






def get_args():
    # need to adjust how parsers are added to require one of the two sub parsers
    # https://stackoverflow.com/questions/23349349/argparse-with-required-subparser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='help for subcommand', dest='convert | process')
    subparsers.required = True
    
    convert = subparsers.add_parser('convert', help='convert a csv to json')
    convert.add_argument('convert',
                        help=f'Convert schedule CSV into JSON file; required headers: "{CSV_HEADERS}"',
                        metavar='/file/to/convert.csv')
    
    process = subparsers.add_parser('process', help='process schedule file')
        
    
    process.add_argument('--schedule_file', '-c', default=None,
                        help='file containing JSON schedule data',
                        metavar='/schedule/file.json',
                        required=True)    

    process.add_argument('--start', '-s', default=None,
                        help='First day of classes in YYYY/MM/DD format', 
                        metavar='"YYYY/MM/DD"',
                        required=True)
    
    process.add_argument('--end', '-e', default=None,
                       help='Last day of classes in YYYY/MM/DD format',
                       metavar = '"YYYY/MM/DD"',
                       required=True)
    
    process.add_argument('--non_instruction', '-n', default=None,
                       help='File containing non-instructional days between start and end date, one per line matching the daytime format (YYYY/MM/DD)',
                       metavar='/path/to/non_instruction.txt',
                       required=True)    
    
    process.add_argument('--date_format', '-d', default='%Y/%m/%d',
                       help='datetime format see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior',
                       metavar='"%Y/%m/%d"', required=False)
    
    
    process.add_argument('--alternate_day', '-a', default=None,
                       help='single day to use "alternate" schedule specified in the schedule file', 
                       metavar="Wednesday")
        
    process.add_argument('--output', '-o', default='~/Desktop',
                       help='Folder to use for output of CSV Schedules (default is ~/Desktop)',
                       metavar='/output/location/')    
    return parser.parse_known_args()






# import sys
# # sys.argv = sys.argv[0:3]
# sys.argv = ['foo.py', 'process']
# # # sys.argv.extend(['--convert', './2021_2022_hs.csv'])
# # # sys.argv.extend(['--convert', './ue.csv'])
# # # sys.argv.extend(['-h'])

# sys.argv.extend(['--start', '2021/08/18', '--end', '2022/06/17'])
# sys.argv.extend(['--non_instruction', './hs_non_instruction_2021-2022.txt'])
# # sys.argv.extend(['--alternate_day', 'Wednesday'])
# # sys.argv.extend(['-c', '/Users/aciuffo/Desktop/foo/2021_2022_hs.json'])
# sys.argv.extend(['--schedule_file', './ue.json'])
# # sys.argv.extend(['--output', '~/Desktop'])






def main():
    args, unknown_args = get_args()

    # run conversion and exit
    if hasattr(args, 'convert'):

        conversion_file = Path(args.convert).expanduser().resolve()
        print(f'converting file: "{conversion_file}"')
        json_output = Path(f"{conversion_file.parent}/{conversion_file.stem}.json")
        csv_to_json(conversion_file, json_output)
        print(f'wrote: {json_output}')
        # bail out after conversion
        do_exit()
    
    non_inst_file = Path(args.non_instruction).expanduser().resolve()
    dt_format = args.date_format

    non_instruction = read_non_instruction(file=non_inst_file, dt_format=dt_format)
    start = args.start
    end = args.end

    schedule_file = Path(args.schedule_file).expanduser().resolve()

    schedule_json = read_json_schedule(schedule_file)

    try:
        alternate_day = WEEKDAYS[args.alternate_day.upper()]
    except AttributeError:
        alternate_day = None
    except KeyError as e:
        do_exit(f'Unknown alternate_day: "{args.alternate_day}"; known alternate days: {WEEKDAYS}', 1)

    output = Path(f'{args.output}/{schedule_file.stem}/').expanduser().resolve()

    try:
        schedule_standard = schedule_json['STANDARD']
        rotation_len = len(schedule_standard)
        rotation_keys = list(schedule_standard.keys())
    except KeyError as e:
        do_exit(f'schedule file "{schedule_file}" is missing a "STANDARD" schedule. Try rebuilding from a .csv schedule', 1)

    try:
        schedule_alternate = schedule_json['ALTERNATE']
    except KeyError:
        if args.alternate_day:
            do_exit(f'schedule file "{schedule_file}" is missing an "ALTERNATE" schedule. Try rebuilding from a .csv schedule and include alternate days.')



    school_days = set_school_days(start=start, end=end, 
                                  non_instruction=non_instruction, dt_format=dt_format)

    # build a list of all the events from lookup dictionaries
    all_events = []
    all_day_events = []

    for idx, date in enumerate(school_days):
        # rot_day is modulo of school-day by number of days in rotation 
        rot_day = idx%rotation_len
        # choose the standard or alternate schedule depending on the day of the week
        if datetime.weekday(date) == alternate_day:
            lookup_schedule = schedule_alternate
        else:
            lookup_schedule = schedule_standard

        all_events.append((date, lookup_schedule[rotation_keys[rot_day]]))
        # build dict for writing out CSV for all-day events
        all_day_events.append({'SUBJECT': f'{rotation_keys[idx%rotation_len]} - Day {idx+1:03d}/{len(school_days)}',
                               'START DATE': datetime.strftime(date, dt_format),
                               'END DATE': datetime.strftime(date, dt_format),
                               'ALL DAY EVENT': 'True'})

    # build a list of all the events from lookup dictionaries
    all_events = []
    all_day_events = []

    for idx, date in enumerate(school_days):
        # rot_day is modulo of school-day by number of days in rotation 
        rot_day = idx%rotation_len
        # choose the standard or alternate schedule depending on the day of the week
        if datetime.weekday(date) == alternate_day:
            lookup_schedule = schedule_alternate
        else:
            lookup_schedule = schedule_standard

        all_events.append((date, lookup_schedule[rotation_keys[rot_day]]))
        # build dict for writing out CSV for all-day events
        all_day_events.append({'SUBJECT': f'{rotation_keys[idx%rotation_len]} - Day {idx+1:03d}/{len(school_days)}',
                               'START DATE': datetime.strftime(date, dt_format),
                               'END DATE': datetime.strftime(date, dt_format),
                               'ALL DAY EVENT': 'True'})

    # build a list of events sorted by type to build CSV files from
    sorted_csv_events = {}
    sorted_csv_events['Rotation Days'] = all_day_events
    for day in all_events:
        this_date = datetime.strftime(day[0], dt_format)
        for event in day[1]:
            if not event['SUBJECT'] in sorted_csv_events:
                sorted_csv_events[event['SUBJECT']] = []
            sorted_csv_events[event['SUBJECT']].append({'START DATE': this_date,
                              'END DATE': this_date,
                              'START TIME': event['START'],
                              'END TIME': event['END'],
                              'SUBJECT': event['SUBJECT'],
                             })

    try:
        output.mkdir(parents='ok', exist_ok=True)
    except OSError as e:
        do_exit(f'Failed to create folder "{output}" due to error {e}')
    for key, value in sorted_csv_events.items():
            csv_fname = output/f'{slugify(key)}.csv'
            with open(csv_fname, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=value[0].keys())
                writer.writeheader()
                for event in value:
                    writer.writerow(event)
    return None






if __name__ == '__main__':
    q = main()









