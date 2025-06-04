import matplotlib
matplotlib.use('Agg')

import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager
import os

# ========== Modern App Header ==========
st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>📊 WhatsApp Chat Analyzer</h1>
    <p style='text-align: center; font-size: 18px;'>Analyze your WhatsApp chats with insights and visuals</p>
    <hr style='border-top: 1px solid #bbb;'>
    """,
    unsafe_allow_html=True
)

# ========== Custom Button CSS ==========
st.markdown("""
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 0.6em 1.2em;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #388E3C;
    }
    </style>
""", unsafe_allow_html=True)

# ========== Sidebar ==========
st.sidebar.markdown(
    """
    <h3 style='color: #4CAF50;'>📂 Upload your chat file</h3>
    """,
    unsafe_allow_html=True
)

uploaded_file = st.sidebar.file_uploader("Choose a file")

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    df = preprocessor.preprocess(data)

    if df is not None and not df.empty:
        user_list = df["user"].unique().tolist()
        if "group_notification" in user_list:
            user_list.remove("group_notification")
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

        if st.sidebar.button("🚀 Show Analysis"):
            # ========== Top Stats ==========
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
            st.subheader("🔢 Top Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Messages", num_messages)
            with col2:
                st.metric("Total Words", words)
            with col3:
                st.metric("Media Shared", num_media_messages)
            with col4:
                st.metric("Links Shared", num_links)

            tab1, tab2, tab3, tab4 = st.tabs(["📈 Timeline", "📅 Activity", "🧠 Word Stats", "😂 Emojis"])

            with tab1:
                st.subheader("Monthly & Daily Timeline")
                timeline = helper.monthly_timeline(selected_user, df)
                fig, ax = plt.subplots()
                ax.plot(timeline["time"], timeline["message"], color="green")
                plt.xticks(rotation="vertical")
                st.pyplot(fig)

                daily_timeline = helper.daily_timeline(selected_user, df)
                fig, ax = plt.subplots()
                ax.plot(daily_timeline["only_date"], daily_timeline["message"], color="black")
                plt.xticks(rotation="vertical")
                st.pyplot(fig)

            with tab2:
                st.subheader("Activity Overview")
                col1, col2 = st.columns(2)

                with col1:
                    st.header("Most Busy Day")
                    busy_day = helper.week_activity_map(selected_user, df)
                    fig, ax = plt.subplots()
                    ax.bar(busy_day.index, busy_day.values, color="purple")
                    plt.xticks(rotation="vertical")
                    st.pyplot(fig)

                with col2:
                    st.header("Most Busy Month")
                    busy_month = helper.month_activity_map(selected_user, df)
                    fig, ax = plt.subplots()
                    ax.bar(busy_month.index, busy_month.values, color="orange")
                    plt.xticks(rotation="vertical")
                    st.pyplot(fig)

                st.header("Weekly Heatmap")
                user_heatmap = helper.activity_heatmap(selected_user, df)
                fig, ax = plt.subplots()
                ax = sns.heatmap(user_heatmap)
                st.pyplot(fig)

                # Show busiest users (group-level only)
                if selected_user == "Overall":
                    st.subheader("🙋‍♂️ Most Busy Users")
                    x, new_df = helper.most_busy_users(df)
                    fig, ax = plt.subplots()
                    col1, col2 = st.columns(2)
                    with col1:
                        ax.bar(x.index, x.values, color="red")
                        plt.xticks(rotation="vertical")
                        st.pyplot(fig)
                    with col2:
                        st.dataframe(new_df)

            with tab3:
                st.subheader("Wordcloud")
                df_wc = helper.create_wordcloud(selected_user, df)
                fig, ax = plt.subplots()
                ax.imshow(df_wc)
                ax.axis("off")
                st.pyplot(fig)

                st.subheader("Most Common Words")
                most_common_df = helper.most_common_words(selected_user, df)
                fig, ax = plt.subplots()
                ax.barh(most_common_df[0], most_common_df[1])
                plt.xticks(rotation="vertical")
                st.pyplot(fig)

            with tab4:
                st.subheader("Emoji Analysis")
                emoji_df = helper.emoji_helper(selected_user, df)
                col1, col2 = st.columns(2)

                with col1:
                    st.dataframe(emoji_df)

                with col2:
                    emoji_font_paths = [
                        "C:\\Windows\\Fonts\\seguiemj.ttf",
                        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                        "/System/Library/Fonts/Apple Color Emoji.ttc"
                    ]
                    prop = None
                    for path in emoji_font_paths:
                        if os.path.exists(path):
                            try:
                                prop = font_manager.FontProperties(fname=path)
                                break
                            except Exception:
                                continue

                    if not emoji_df.empty:
                        fig, ax = plt.subplots()
                        ax.bar(emoji_df[0].head(10), emoji_df[1].head(10), color="skyblue")
                        ax.set_title("Top Emojis", fontproperties=prop)
                        ax.set_xlabel("Emoji", fontproperties=prop)
                        ax.set_ylabel("Frequency")
                        if prop:
                            for label in ax.get_xticklabels():
                                label.set_fontproperties(prop)
                        st.pyplot(fig)
                    else:
                        st.write("No emojis found.")

    elif df is None:
        st.error("Failed to process the chat file. Please check the file format and ensure it contains valid data.")
    else:
        st.warning("The processed chat data is empty. This might be due to date format issues or an empty chat file.")
