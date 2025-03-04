import json
import os
import glob
import pandas as pd
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from nltk.corpus import stopwords
from datetime import datetime
import argparse
import io
import shutil
import copy
from pick import pick
from time import sleep

class SlackDataProcessor:
    def __init__(self):
        pass
    def slack_parser(self, path_channel):
        """ parse slack data to extract useful informations from the json file
            step of execution
            1. Import the required modules
            2. read all json file from the provided path
            3. combine all json files in the provided path
            4. extract all required informations from the slack data
            5. convert to dataframe and merge all
            6. reset the index and return dataframe
        """

        # specify path to get json files
        combined = []
        for json_file in glob.glob(f"{path_channel}*.json"):
            with open(json_file, 'r', encoding="utf8") as slack_data:
                data=json.load(slack_data)
                combined.append(slack_data)

        # loop through all json files and extract required informations
        dflist = []
        for slack_data in combined:

            msg_type, msg_content, sender_id, time_msg, msg_dist, time_thread_st, reply_users, \
            reply_count, reply_users_count, tm_thread_end = [],[],[],[],[],[],[],[],[],[]

            for row in slack_data:
                if 'bot_id' in row.keys():
                    continue
                else:
                    msg_type.append(row['type'])
                    msg_content.append(row['text'])
                    if 'user_profile' in row.keys(): sender_id.append(row['user_profile']['real_name'])
                    else: sender_id.append('Not provided')
                    time_msg.append(row['ts'])
                    if 'blocks' in row.keys() and len(row['blocks'][0]['elements'][0]['elements']) != 0 :
                        msg_dist.append(row['blocks'][0]['elements'][0]['elements'][0]['type'])
                    else: msg_dist.append('reshared')
                    if 'thread_ts' in row.keys():
                        time_thread_st.append(row['thread_ts'])
                    else:
                        time_thread_st.append(0)
                    if 'reply_users' in row.keys(): reply_users.append(",".join(row['reply_users'])) 
                    else:    reply_users.append(0)
                    if 'reply_count' in row.keys():
                        reply_count.append(row['reply_count'])
                        reply_users_count.append(row['reply_users_count'])
                        tm_thread_end.append(row['latest_reply'])
                    else:
                        reply_count.append(0)
                        reply_users_count.append(0)
                        tm_thread_end.append(0)
            data = zip(msg_type, msg_content, sender_id, time_msg, msg_dist, time_thread_st,
            reply_count, reply_users_count, reply_users, tm_thread_end)
            columns = ['msg_type', 'msg_content', 'sender_name', 'msg_sent_time', 'msg_dist_type',
            'time_thread_start', 'reply_count', 'reply_users_count', 'reply_users', 'tm_thread_end']

            df = pd.DataFrame(data=data, columns=columns)
            df = df[df['sender_name'] != 'Not provided']
            dflist.append(df)

        dfall = pd.concat(dflist, ignore_index=True)
        dfall['channel'] = path_channel.split('/')[-1].split('.')[0]        
        dfall = dfall.reset_index(drop=True)
        
        return dfall    

    def parse_slack_reaction(self, path, channel):
        """get reactions"""
        dfall_reaction = pd.DataFrame()
        combined = []
        for json_file in glob.glob(f"{path}*.json"):
            with open(json_file, 'r') as slack_data:
                combined.append(slack_data)

        reaction_name, reaction_count, reaction_users, msg, user_id = [], [], [], [], []

        for k in combined:
            slack_data = json.load(open(k.name, 'r', encoding="utf-8"))
            
            for i_count, i in enumerate(slack_data):
                if 'reactions' in i.keys():
                    for j in range(len(i['reactions'])):
                        msg.append(i['text'])
                        user_id.append(i['user'])
                        reaction_name.append(i['reactions'][j]['name'])
                        reaction_count.append(i['reactions'][j]['count'])
                        reaction_users.append(",".join(i['reactions'][j]['users']))
                    
        data_reaction = zip(reaction_name, reaction_count, reaction_users, msg, user_id)
        columns_reaction = ['reaction_name', 'reaction_count', 'reaction_users_count', 'message', 'user_id']
        df_reaction = pd.DataFrame(data=data_reaction, columns=columns_reaction)
        df_reaction['channel'] = channel
        return df_reaction

    def get_community_participation(self,path):
        """ specify path to get json files"""
        combined = []
        comm_dict = {}
        for json_file in glob.glob(f"{path}*.json"):
            with open(json_file, 'r') as slack_data:
                combined.append(slack_data)
        # print(f"Total json files is {len(combined)}")
        for i in combined:
            a = json.load(open(i.name, 'r', encoding='utf-8'))

            for msg in a:
                if 'replies' in msg.keys():
                    for i in msg['replies']:
                        comm_dict[i['user']] = comm_dict.get(i['user'], 0)+1
        return comm_dict

    def convert_2_timestamp(self,column, data):
        """convert from unix time to readable timestamp
            args: column: columns that needs to be converted to timestamp
                    data: data that has the specified column
        """
        if column in data.columns.values:
            timestamp_ = []
            for time_unix in data[column]:
                if time_unix == 0:
                    timestamp_.append(0)
                else:
                    a = datetime.datetime.fromtimestamp(float(time_unix))
                    timestamp_.append(a.strftime('%Y-%m-%d %H:%M:%S'))
            return timestamp_
        else: 
            print(f"{column} not in data")

    def get_tagged_users(self,df):
        """get all @ in the messages"""

        return df['msg_content'].map(lambda x: re.findall(r'@U\w+', x))

    def map_userid_2_realname(self,user_profile: dict, comm_dict: dict, plot=False):
        """
        map slack_id to realnames
        user_profile: a dictionary that contains users info such as real_names
        comm_dict: a dictionary that contains slack_id and total_message sent by that slack_id
        """
        user_dict = {} # to store the id
        real_name = [] # to store the real name
        ac_comm_dict = {} # to store the mapping
        count = 0
        # collect all the real names
        for i in range(len(user_profile['profile'])):
            real_name.append(dict(user_profile['profile'])[i]['real_name'])

        # loop the slack ids
        for i in user_profile['id']:
            user_dict[i] = real_name[count]
            count += 1

        # to store mapping
        for i in comm_dict:
            if i in user_dict:
                ac_comm_dict[user_dict[i]] = comm_dict[i]

        ac_comm_dict = pd.DataFrame(data= zip(ac_comm_dict.keys(), ac_comm_dict.values()),
        columns=['LearnerName', '# of Msg sent in Threads']).sort_values(by='# of Msg sent in Threads', ascending=False)
        
        if plot:
            ac_comm_dict.plot.bar(figsize=(15, 7.5), x='LearnerName', y='# of Msg sent in Threads')
            plt.title('Student based on Message sent in thread', size=20)
            
        return ac_comm_dict


class SlackDataLoader:
    '''
    Slack exported data IO class.

    When you open slack exported ZIP file, each channel or direct message 
    will have its own folder. Each folder will contain messages from the 
    conversation, organised by date in separate JSON files.

    You'll see reference files for different kinds of conversations: 
    users.json files for all types of users that exist in the slack workspace
    channels.json files for public channels, 
    
    These files contain metadata about the conversations, including their names and IDs.

    For secruity reason, we have annonymized names - the names you will see are generated using faker library.
    
    '''
    def __init__(self, path):
        self.path = path
        self.channels = self.get_channels()
        self.users = self.get_users()

    def get_users(self):
        '''
        write a function to get all the users from the json file
        '''
        with open(os.path.join(self.path, 'users.json'), 'r') as f:
            users = json.load(f)

        return users
    
    def get_channels(self):
        '''
        write a function to get all the channels from the json file
        '''
        with open(os.path.join(self.path, 'channels.json'), 'r') as f:
            channels = json.load(f)

        return channels
    def get_channel_messages(self, channel_name):
        # ... (the rest of the function)
        return 0

    def get_user_map(self):
        '''
        write a function to get a map between user id and user name
        '''
        userNamesById = {}
        userIdsByName = {}
        for user in self.users:
            userNamesById[user['id']] = user['name']
            userIdsByName[user['name']] = user['id']
        return userNamesById, userIdsByName        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Slack history')

    
    parser.add_argument('--zip', help="Name of a zip file to import")
    args = parser.parse_args()
