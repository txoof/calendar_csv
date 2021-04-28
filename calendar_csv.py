#!/usr/bin/env python3
# coding: utf-8







import csv
# remove this and move to just argparse -- use only standard modules
# import ArgConfigParse
import textwrap
from dateutil import rrule
from datetime import datetime
from datetime import timedelta
import logging
from pathlib import Path
import json
import argparse
from sys import exit
from sys import argv






WEEKDAYS = {
    'MONDAY': 0,
    'TUESDAY': 1,
    'WEDNESDAY': 2,
    'THURSDAY': 3,
    'FRIDAY': 4,
    'SATURDAY': 5,
    'SUNDAY': 6
}






def do_exit(msg=None, level=0):
    if level > 0:
        
        print(f'exiting due to error:\n     {msg}')
    elif msg:
        print(f'{msg}')
        print('exiting')
    exit(level)
    






def build_empty_schedule(days, blocks):
    '''build a JSON compatible dictionary with all required schedule fields
    Args:
        days(`int`): number of days in a cycle
        blocks(`int`): total number of blocks in a day (including breaks, lunch, etc.)
        
    Returns:
        dict'''
    template_day = {}
    blocks_list = []
    block = {'name': '', 
              'start': '00:00',
              'duration': 0}
    for j in range(0, blocks):
        blocks_list.append(block)

    for i in range(0, days):
        template_day[f'day_{i+1}'] = blocks_list
    return {'standard': template_day, 'alternate': template_day}






def write_empty_schedule(file, days, blocks):
    '''write empty JSON formatted schedule to `file`
    Args:
        file(`Path`): path to write
        days(`int`): number of days in a cycle
        blocks(`int`): total number of blocks in a day including breaks, lunch, etc.
        
    Returns:
        `Path`'''
    
    if Path(file).exists():
        raise FileExistsError(f'{file} already exits, refusing to over-write')
#     json_data = json.dumps(build_empty_schedule())
    with open(file, 'w') as outfile:
        json.dump(build_empty_schedule(days, blocks), outfile, indent=5)
    return file






def read_non_instruction(file, dt_format):
    '''return list of daytime objects based on dates in file
    
    Args:
        file(`str` or `Path`): file to read'''
    # read vacation/non instructional days list
    errors = []
    with open(file, 'r') as open_file:
        file_txt = open_file.readlines()

    non_instruction_dt = []
    for idx, val in enumerate(file_txt):
        try:
            non_instruction_dt.append(datetime.strptime(val.strip(), dt_format))
        except ValueError as e:
            # capture all the errors
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
            print(f'\tline: {each[0]+1} -- "{each[1].rstrip()}"')
        print('='*40)
        do_exit(f'unexpected date formats in "{file}".', 1)
#             do_exit(f'unknown date format in file {file} line {idx+1}: "{val}" \n expected format: "{dt_format}"', 1)
        
    return non_instruction_dt

    






def read_schedule_json(file):
    '''read a json formatted file
    Args:
        file(`Path`): file to read
    
    Returns:
        `dict`'''
    try:
        with open(file, 'r') as json_file:
            json_data = json.load(json_file)
    except Exception as e:
        do_exit(f'failed to read json file "{file}": {e}', 1)
    
    return json_data






def set_school_days(start, end, non_instruction, dt_format):
    '''create a list of school days excluding weekends and non-instructional days
    Args:
        start(`str`): first day of school - in dt_format (e.g. 2021/08/17)
        end(`str`): last day of school - in dt_format (e.g. 2022/06/18)
        non_instruction(`list`): list of non-instructional days in dt_format
        dt_format(`str`): datetime format e.g. %Y/%m/%d
        
    Returns:
        `list`
        '''
    
    start_dt = datetime.strptime(start, dt_format)
    end_dt = datetime.strptime(end, dt_format)
    
    # set actual school days
    school_days = []
    for dt in rrule.rrule(rrule.DAILY, dtstart=start_dt, until=end_dt):
        if dt not in non_instruction and datetime.weekday(dt) in range(0, 5):
                school_days.append(dt)
                
    return school_days
        






def get_events(dicts):
    '''process list of of dicts and return all unique `name` values
    Args:
        dicts(`list` of `dict`): list of dictionaries containing key "name"
        
    Returns:
        `set` of name'''
    if not isinstance(dicts, list):
        raise TypeError(f'expected list of dictionaries, recieved {type(dicts)}')
    events_unique = set()
    for d in dicts:
        for day, schedule in d.items():
            for event in schedule:
                events_unique.add(event['name'])
    return(events_unique)






def day_schedule(l, date):
    '''return a google calendar compatible list of dict for writing CSVs
    
    Args:
        l(`list`): list of all blocks from a single day
        date(`str`): date string e.g. 2021/08/17
        
    Returns:
        `list of dict` '''
    dt_format = '%H:%M'
    schedule = []
    for idx, val in enumerate(l):
        subject = val['name']
        start_date = date
        start_time = val['start']
        start_dt = datetime.strptime(start_time, dt_format)
        end_dt = start_dt + timedelta(minutes = val['duration'])
        end_time = datetime.strftime(end_dt, dt_format)
        event = {
            'Subject': subject,
            'Start Date': start_date,
            'Start Time': start_time,
            'End Time': end_time
        }
        schedule.append(event)
    return schedule






def write_csv(filename, title, events):
    '''write a csv file for all events that match "title"
    
    Args: 
        filename(`Path`): file to write
        title(`str`): string to match in event Subject e.g. "Block C"
        events(`list` of `dict`)
        
    Returns: 
        `bool`: true on success
    '''
    # create output dir if it doesn't already exist
    if not filename.parent.exists():
        Path(filename.parent).mkdir(parents=True)
        
    with open(filename, 'w') as csvfile:
        fieldnames = events[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            if title == '*':
                writer.writerow(event)
            elif title in event['Subject']:
                writer.writerow(event)
                
    return True 






def get_args():
    epilog_text = textwrap.dedent(f'''    Usage Help:
    
    EXAMPLE: GENERATING CSV FOR GOOGLE CALENDAR

        ${argv[0]} --start_date 2021/08/18 --end_date 2022/06/17 \\
        --schedule_file ~/Desktop/hs_block.JSON \\
        --non_instruction ~/Desktop/2021-2022_noninstruction_days.txt \\
        --alternate_day Wednesday \\
        --output_path ~/Desktop/hs_block/ \\
        ''')
    
    
    parser = argparse.ArgumentParser(description='process command line arguments',
                                    formatter_class=argparse.RawDescriptionHelpFormatter,
                                    epilog=epilog_text)
    parser.add_argument('-s', '--start_date', default=None,
                       help='First day of classes in YYYY/MM/DD format', metavar='"YYYY/MM/DD"')
    parser.add_argument('-e', '--end_date', default=None,
                        help='Last day of classes in YYYY/MM/DD format', metavar='"YYYY/MM/DD"')
    parser.add_argument('-n', '--non_instruction', default=None,
                       help='File containing non-instructional days between start and end date, one per line matching the daytime format (YYYY/MM/DD)')
    parser.add_argument('-c', '--schedule_file', default=None,
                        help='file containing JSON schedule data')
    parser.add_argument('-d', '--date_format', default='%Y/%m/%d',
                       help='datetime format see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior',
                       metavar='"%Y/%m/%d"')
    parser.add_argument('-a', '--alternate_day', default=None,
                       help='single day to use "alternate" schedule specified in the schedule file', metavar="Wednesday")
    parser.add_argument('-o', '--output_path', default='~/Desktop/',
                       help='location to output CSV files')
    parser.add_argument('-b', '--blank_schedule', default=None,
                       help='generate a blank JSON schedule file template on the Desktop using supplied name with `--days` in the rotation with `--blocks` per day.',
                       metavar='filename')
    parser.add_argument('--days', default=8, 
                       help='number of days in a rotation (see also --blank_schedule and --blocks)')
    parser.add_argument('--blocks', default=8,
                       help='number of blocks per day (see also --blank_schedule and --days)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                       help='increase verbosity in logging (additional -v increases level)')
    
    return parser.parse_known_args()






# argv = argv[0:3]
# argv

# argv.extend(['-s', '2021/08/18'])

# argv.extend(['-e', '2022/06/17'])

# argv.extend(['-n', './vacation_days.txt'])


# argv.extend(['-c', './schedule.json', '-a', 'Wednesday'])

# argv.extend(['-o', '~/Desktop/calendar_csv/'])

# argv.extend(['-v', '-v'])






def main():
    args, unknown_args = get_args()
    log_level = 40
    if args.verbose:
        log_level = log_level-(args.verbose*10)
    logging.root.setLevel(log_level)

    # create a blank schedule 
    if args.blank_schedule:
        try:
            write_empty_schedule(Path(args.blank_schedule+'.JSON').expanduser(), blocks=args.blocks,
                                days=args.days)
            do_exit(f'wrote blank schedule to {file}.JSON')
        except (FileExistsError, OSError) as e:
            do_exit(e, 1)

    # set file with non-instruction days
    if args.non_instruction:
        file_non_instruction = Path(args.non_instruction).expanduser()  
    else:
        do_exit('no non-instructional days file provided; cannot continue')  
    try:  
        non_instruction = read_non_instruction(file_non_instruction, dt_format=args.date_format)
    except OSError as e:
        do_exit(e, 1)

    # set schedule file
    if args.schedule_file:
        file_schedule = Path(args.schedule_file).expanduser()
    else:
        do_exit('no schedule file provided; cannot continue')
    try:
        schedule_json = read_schedule_json(file_schedule)
    except OSError as e:
        do_exit(e, 1)

    # set output path
    if args.output_path:
        output_path = Path(args.output_path).expanduser()
    else:
        do_exit('no output path supplied; cannot continue')

    # set alternate day
    if args.alternate_day:
        try:
            alternate_day = WEEKDAYS[str(args.alternate_day).upper()]
        except KeyError:
            do_exit(f'ERROR: {args.alternate_day} is not a valid alternate day. Valid choices are: {WEEKDAYS.keys()}')
    else:
        alternate_day = None

    # set start & end date
    if args.start_date:
        sy_start = args.start_date
    else:
        do_exit(f'no school-year start date provided; cannot continue')

    if args.end_date:
        sy_end = args.end_date
    else:
        do_exit(f'no school-year end date provided; cannot continue ')

    # check date format for daytime conversions
    if not args.date_format:
        do_exit('no date format provided; cannot continue. HINT: try removing the -d/--date_format arguments')
    else:
        date_format = args.date_format


    # set standard and alternate schedules:
    try:
        schedule_standard = schedule_json['standard']
        rotation_len = len(schedule_standard)
        if alternate_day:
            schedule_alternate = schedule_json['alternate']
    except KeyError as e:
        do_exit(f'{file_schedule} missing section: {e}\nTry regenerating the schedule file from scratch (--blank)', 1)


    # create a list of all unique events
    unique_events = get_events([schedule_standard, schedule_alternate])

    # build a list of all school days
    school_days = set_school_days(start=sy_start, end=sy_end, dt_format=date_format, non_instruction=non_instruction)

    # build a list of all events
    all_events = []
    # build a list of all school days -- use this to produce a CSV of all-day events
    day_list = []
    for idx, val in enumerate(school_days):
        # set standard schedule by default
        schedule_lookup = schedule_standard
        if alternate_day:
            if datetime.weekday(val) == alternate_day:
                schedule_lookup = schedule_alternate
        date = datetime.strftime(val, date_format)
        day = sorted(schedule_lookup)[idx%rotation_len]
        this_day = day_schedule(schedule_lookup[day], date)
        all_events.extend(this_day)
        day_list.append({'Subject': f'{day} - instructional day: {idx+1}',
                         'Start Date': date,
                         'End Date': date,
                         'All Day Event': 'True'})

    # # write out a CSV for each unique schedule
    for event in unique_events:
        output_file = Path(output_path/f'{file_schedule.stem}_{event}.csv')
        try:
            write_csv(output_file, event, all_events)
        except OSError as e:
            do_exit(f'error writing to {output_file}: {e}', 1)
    write_csv(Path(output_path/f'{file_schedule.stem}_all events.csv'), '*', all_events)
    write_csv(Path(output_path/f'{file_schedule.stem}_all_day_events.csv'), '*', day_list)






# def days_to_csv(days_list):
#     event_dict = {
#         'Subject': None,
#         'Start Date': None,
#         'End Date': None,
#         'All Day Event': True,
#     }
#     day_csv = []
#     for i in days_list:
#         day_csv.append({
#         })
        






if __name__ == '__main__':
    s = main()






# def parse_schedules(schedule_dict):
#     # parse schedule file into lookup tables
#     if not isinstance(schedule_dict, dict):
#         raise TypeError (f'schedule_dict must be of type(dict), not {type(schedule_dict)}')
#     schedule_mttf = {} 
#     schedule_w = {}
#     for key, value in schedule_dict.items():
#         if key.startswith('%'):
#             if 'wednesday' in key:
#                 schedule_w[key] = value
#             else:
#                 schedule_mttf[key] = value
#         else:
#             logging.warning(f'unrecongized "day" item in confiuration file(s) {schedule.config_files}: {key}')
#             logging.info(f'all "day" items must follow the format "[%day N] or "[%day N wednesday]"') 
#     return(schedule_mttf, schedule_w)


