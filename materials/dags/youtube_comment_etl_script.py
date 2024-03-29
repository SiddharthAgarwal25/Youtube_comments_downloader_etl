from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import boto3
def run_etl(api_key, playlist_ids):
    api_key = api_key
    playlist_ids = [playlist_ids]

    youtube = build('youtube', 'v3', developerKey=api_key)

    def get_all_video_ids_from_playlists(youtube, playlist_ids):
        all_videos = []  # Initialize a single list to hold all video IDs

        for playlist_id in playlist_ids:
            next_page_token = None

            # Fetch videos from the current playlist
            while True:
                playlist_request = youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token)
                playlist_response = playlist_request.execute()

                all_videos += [item['contentDetails']['videoId'] for item in playlist_response['items']]

                next_page_token = playlist_response.get('nextPageToken')

                if next_page_token is None:
                    break

        return all_videos

    # Fetch all video IDs from the specified playlists
    video_ids = get_all_video_ids_from_playlists(youtube, playlist_ids)


    def get_replies(youtube, parent_id, video_id):  # Added video_id as an argument
        replies = []
        next_page_token = None

        while True:
            reply_request = youtube.comments().list(
                part="snippet",
                parentId=parent_id,
                textFormat="plainText",
                maxResults=100,
                pageToken=next_page_token
            )
            reply_response = reply_request.execute()

            for item in reply_response['items']:
                comment = item['snippet']
                replies.append({
                    'Timestamp': comment['publishedAt'],
                    'Username': comment['authorDisplayName'],
                    'VideoID': video_id,
                    'Comment': comment['textDisplay'],
                    'Date': comment['updatedAt'] if 'updatedAt' in comment else comment['publishedAt']
                })

            next_page_token = reply_response.get('nextPageToken')
            if not next_page_token:
                break

        return replies

    # Function to get all comments (including replies) for a single video
    def get_comments_for_video(youtube, video_id):
        all_comments = []
        next_page_token = None

        while True:
            comment_request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                pageToken=next_page_token,
                textFormat="plainText",
                maxResults=100
            )
            comment_response = comment_request.execute()

            for item in comment_response['items']:
                top_comment = item['snippet']['topLevelComment']['snippet']
                all_comments.append({
                    'Timestamp': top_comment['publishedAt'],
                    'Username': top_comment['authorDisplayName'],
                    'VideoID': video_id,  # Directly using video_id from function parameter
                    'Comment': top_comment['textDisplay'],
                    'Date': top_comment['updatedAt'] if 'updatedAt' in top_comment else top_comment['publishedAt']
                })

                # Fetch replies if there are any
                if item['snippet']['totalReplyCount'] > 0:
                    all_comments.extend(get_replies(youtube, item['snippet']['topLevelComment']['id'], video_id))

            next_page_token = comment_response.get('nextPageToken')
            if not next_page_token:
                break

        return all_comments

    # List to hold all comments from all videos
    all_comments = []


    for video_id in video_ids:
        video_comments = get_comments_for_video(youtube, video_id)
        all_comments.extend(video_comments)

    # Create DataFrame
    comments_df = pd.DataFrame(all_comments)
    print(comments_df)
    csv_file_path = "youtube_comments_data.csv"
    aws_access_key_id = ''
    aws_secret_access_key = ''
    comments_df.to_csv(csv_file_path, index=False)
    s3_bucket_name = "youtube-airflow-proj"
    s3_key = "youtube_comments_data.csv"
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    s3_client.upload_file(csv_file_path, s3_bucket_name, s3_key)

    return comments_df


# run_etl()
