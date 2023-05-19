import sys
import datetime

def validate_input(date_input):
    """
    Validate input for date_input and exit if validation fails. This function is used to validate user input before saving to database
   
    @param date_input - date input to be
    """
    try:
        datetime.datetime.strptime(date_input, '%Y%m%d')
    except ValueError:
        raise ValueError("Input parameter should be YYYYMMDD")
        sys.exit(1)