import re
import pandas as pd

def preprocess(data):
    # Pattern to split messages based on WhatsApp timestamp format
    # Updated to handle dd/mm/yyyy, h:mm[space or non-breaking space]am/pm - format
    # Example: 02/03/2025, 9:30\u202fam - 
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?:\s|\u202f)(?:am|pm)\s-\s'
    
    # Split the data into messages based on the pattern. Index [1:] skips the first empty element.
    messages_data = re.split(pattern, data)[1:]
    # Find all occurrences of the pattern to get the dates
    dates_data = re.findall(pattern, data)

    # Create an empty DataFrame structure to return in case of errors
    empty_df = pd.DataFrame(columns=[
        'date', 'user', 'message', 'only_date', 'year', 'month_num',
        'month', 'day', 'day_name', 'hour', 'minute', 'period'
    ])

    # Ensure equal number of messages and dates before creating DataFrame
    min_len = min(len(messages_data), len(dates_data))
    if min_len == 0:
        print("Warning: No messages or dates could be extracted using the specific format. Check the input file format and the pattern in preprocessor.py.")
        return empty_df # Return empty DataFrame if no data extracted

    df = pd.DataFrame({'user_message': messages_data[:min_len], 'message_date': dates_data[:min_len]})

    # Attempt to convert message_date to datetime using the specific format found
    try:
        # Format for dd/mm/yyyy, h:mm[non-breaking space]am/pm - 
        df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %I:%M\u202f%p - ')
    except ValueError:
        try:
            # Fallback: Try format with regular space before am/pm
            df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %I:%M %p - ')
        except ValueError:
             try:
                 # Fallback: Try format without AM/PM (24-hour)
                 df['date'] = pd.to_datetime(df['message_date'], format='%d/%m/%Y, %H:%M - ')
             except ValueError as e:
                 print(f"Error parsing dates: {e}. Could not match known formats including the specific Instamart format. Please double-check the date format in your chat file and adjust the format strings in preprocessor.py.")
                 # Return an empty DataFrame instead of None to prevent app crash
                 return empty_df

    df.drop(columns=['message_date'], inplace=True)

    # Extract users and messages from user_message
    users = []
    messages_list = []
    for message in df['user_message']:
        # Ensure message is a string and not empty before processing
        if not isinstance(message, str) or not message.strip():
            # Handle empty/non-string messages (e.g., skip or log)
            users.append('skipped_entry')
            messages_list.append('')
            continue

        # Split message into sender and message content
        # Pattern looks for 'Sender Name: '
        entry = re.split('([\w\W]+?):\s', message, maxsplit=1) # Use maxsplit=1
        if len(entry) > 1 and entry[1] is not None:  # Check if split occurred and sender part exists
            users.append(entry[1].strip()) # Append sender name
            # Check if there is message content after the split
            if len(entry) > 2 and entry[2] is not None:
                 messages_list.append(entry[2].strip()) # Append message content
            else:
                 messages_list.append('') # Append empty if no message content after sender
        else: # Likely group notification or line without 'Sender: '
            # Check if it's the initial Meta security message
            if message.strip().startswith("This business uses a secure service from Meta"):
                users.append('system_notification')
                messages_list.append(message.strip())
            else:
                users.append('group_notification') # Assume other non-matching are notifications
                messages_list.append(entry[0].strip()) # Append the original line content

    df['user'] = users
    df['message'] = messages_list
    df.drop(columns=['user_message'], inplace=True)

    # Extract date and time components
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # Create time period buckets
    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(f"{hour}-00")
        elif hour == 0:
            period.append(f"00-01")
        else:
            period.append(f"{hour}-{hour + 1}")
    df['period'] = period

    return df

