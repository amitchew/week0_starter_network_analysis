import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt

def upload_slack_file():
    uploaded_file = st.file_uploader("Upload your Slack message analysis file (JSON)", type=["json"])

    if uploaded_file is not None:
        st.success("File uploaded successfully!")

        # Read the uploaded JSON file
        content = uploaded_file.read()
        data = json.loads(content)

        # Convert JSON data to DataFrame
        df = pd.json_normalize(data)

        # Display the DataFrame
        st.write("Displaying the content of the uploaded file:")
        st.write(df)

        # Plotting options
        st.subheader("Plotting Options:")
        plot_option = st.selectbox("Select Plotting Option", ["Top Users by Reply Count", "Reply Counts per User per Channel"])

        if plot_option == "Top Users by Reply Count":
            plot_top_users_by_reply_count(df)
        elif plot_option == "Reply Counts per User per Channel":
            plot_reply_counts_per_user_per_channel(df)

def plot_top_users_by_reply_count(df):
    user_reply_counts = df.groupby('sender_name')['reply_count'].sum()
    sorted_user_reply_counts = user_reply_counts.sort_values(ascending=False)

    # Plot the top users by reply count
    plt.figure(figsize=(15, 7.5))
    sorted_user_reply_counts.plot(kind='bar')
    
    plt.title('Top Users by Reply Counts')
    plt.xlabel('User')
    plt.ylabel('Number of Replies')
    st.pyplot()

def plot_reply_counts_per_user_per_channel(df):
    user_channel_reply_counts = df.groupby(['channel', 'sender_name'])['reply_count'].sum().unstack()

    # Plot the reply counts per user per channel
    plt.figure(figsize=(15, 7.5))
    user_channel_reply_counts.plot(kind='bar', stacked=True)
    
    plt.title('Reply Counts of User/Channel')
    plt.xlabel('Channel')
    plt.ylabel('Number of Replies')
    plt.legend(title='Sender Name', bbox_to_anchor=(1, 1))
    st.pyplot()

def main():
    st.title("Slack Message Analysis App")
    st.sidebar.header("Navigation")

    app_mode = st.sidebar.selectbox("Choose the app mode", ["Upload File", "About"])

    if app_mode == "Upload File":
        st.header("Upload Slack Message Analysis File")
        upload_slack_file()
    elif app_mode == "About":
        st.header("About")
        st.write(
            "This Streamlit app allows you to upload a Slack message analysis file in JSON format and displays its contents."
        )

if __name__ == "__main__":
    main()
