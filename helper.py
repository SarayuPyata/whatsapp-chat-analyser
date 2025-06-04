from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji

extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # fetch the number of messages
    num_messages = df.shape[0]

    # fetch the total number of words
    words = []
    for message in df["message"]:
        words.extend(message.split())

    # fetch number of media messages
    # More flexible check for common media message markers
    num_media_messages = df[df["message"].str.lower().str.contains("media omitted", na=False)].shape[0]

    # fetch number of links shared
    links = []
    for message in df["message"]:
        links.extend(extract.find_urls(message))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df["user"].value_counts().head()
    # Calculate percentage relative to total messages, excluding group notifications if necessary
    # Consider filtering out group_notification before calculating total shape if it shouldn't count
    total_messages = df[df["user"] != "group_notification"].shape[0]
    if total_messages == 0:
        total_messages = df.shape[0] # Avoid division by zero if only notifications exist
        if total_messages == 0:
             return x, pd.DataFrame({"name": [], "percent": []}) # Handle empty df case

    df_percent = round((df["user"].value_counts() / total_messages) * 100, 2).reset_index()
    # Ensure column names are consistent after reset_index
    df_percent.columns = ["name", "percent"] # Explicitly name columns

    return x, df_percent

def create_wordcloud(selected_user, df):
    try:
        with open("stop_hinglish.txt", "r") as f:
            stop_words = f.read()
    except FileNotFoundError:
        print("Warning: stop_hinglish.txt not found. Proceeding without stop words.")
        stop_words = []

    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Filter out group notifications and media messages
    temp = df[df["user"] != "group_notification"]
    temp = temp[temp["message"] != "<Media omitted>\n"]

    # Handle empty data after filtering
    if temp.empty:
        print("Warning: No text messages found for word cloud generation.")
        # Return an empty WordCloud object or handle as appropriate
        return WordCloud(width=500,height=500,min_font_size=10,background_color='white').generate('')

    def remove_stop_words(message):
        y = []
        # Ensure message is a string
        if isinstance(message, str):
            for word in message.lower().split():
                if word not in stop_words:
                    y.append(word)
        return " ".join(y)

    # Apply stop word removal
    # Use .loc to avoid SettingWithCopyWarning
    temp.loc[:, "message"] = temp["message"].apply(remove_stop_words)

    # Concatenate messages for word cloud
    text_for_wc = temp["message"].str.cat(sep=" ")

    # Handle empty text after stop word removal
    if not text_for_wc.strip():
        print("Warning: No words left after removing stop words.")
        return WordCloud(width=500,height=500,min_font_size=10,background_color='white').generate('')

    wc = WordCloud(width=500, height=500, min_font_size=10, background_color="white")
    df_wc = wc.generate(text_for_wc)
    return df_wc

def most_common_words(selected_user, df):
    try:
        with open("stop_hinglish.txt", "r") as f:
            stop_words = f.read()
    except FileNotFoundError:
        print("Warning: stop_hinglish.txt not found. Proceeding without stop words.")
        stop_words = []

    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    temp = df[df["user"] != "group_notification"]
    temp = temp[temp["message"] != "<Media omitted>\n"]

    words = []
    for message in temp["message"]:
         # Ensure message is a string
        if isinstance(message, str):
            for word in message.lower().split():
                if word not in stop_words:
                    words.append(word)

    # Handle case where no words are found
    if not words:
        return pd.DataFrame(columns=[0, 1]) # Return empty DataFrame

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

def emoji_helper(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    emojis = []
    for message in df["message"]:
        # Ensure message is a string before iterating
        if isinstance(message, str):
            # Updated method using emoji.is_emoji()
            emojis.extend([c for c in message if emoji.is_emoji(c)])

    # Handle case where no emojis are found
    if not emojis:
        return pd.DataFrame(columns=[0, 1]) # Return empty DataFrame with expected columns

    emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
    return emoji_df

def monthly_timeline(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Ensure 'date' column exists and is datetime type
    if 'date' not in df.columns or not pd.api.types.is_datetime64_any_dtype(df['date']):
        print("Error: 'date' column missing or not datetime type in monthly_timeline.")
        # Return empty DataFrame or handle error appropriately
        return pd.DataFrame(columns=['time', 'message'])

    timeline = df.groupby(["year", "month_num", "month"]).count()["message"].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline["month"][i] + "-" + str(timeline["year"][i]))

    timeline["time"] = time
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Ensure 'only_date' column exists
    if 'only_date' not in df.columns:
        print("Error: 'only_date' column missing in daily_timeline.")
        return pd.DataFrame(columns=['only_date', 'message'])

    daily_timeline = df.groupby("only_date").count()["message"].reset_index()
    return daily_timeline

def week_activity_map(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]
    # Ensure 'day_name' column exists
    if 'day_name' not in df.columns:
         print("Error: 'day_name' column missing in week_activity_map.")
         return pd.Series(dtype=int) # Return empty Series
    return df["day_name"].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]
    # Ensure 'month' column exists
    if 'month' not in df.columns:
        print("Error: 'month' column missing in month_activity_map.")
        return pd.Series(dtype=int) # Return empty Series
    return df["month"].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != "Overall":
        df = df[df["user"] == selected_user]

    # Ensure required columns exist
    if not all(col in df.columns for col in ['day_name', 'period', 'message']):
        print("Error: Required columns ('day_name', 'period', 'message') missing for heatmap.")
        # Return an empty pivot table or handle appropriately
        return pd.DataFrame()

    # Filter out potential non-string messages before pivot
    df_filtered = df[df['message'].apply(lambda x: isinstance(x, str))]
    if df_filtered.empty:
        print("Warning: No valid messages found for heatmap generation after filtering.")
        return pd.DataFrame()

    user_heatmap = df_filtered.pivot_table(index="day_name", columns="period", values="message", aggfunc="count").fillna(0)
    return user_heatmap
