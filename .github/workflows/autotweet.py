import os
import sys
import random
import requests
import time
import tweepy
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime

# --- API Keys are now read from GitHub's secure Secrets vault ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- YOUR CURATED LIST of 50 streamers and personalities ---
STREAMER_LIST = [
    "Kai Cenat", "rayasianboy", "DDG", "totaamc", "2xRaKai", "indialovewestbrooks", 
    "Thetylilshow", "funnymike", "Anyme023", "wendolynortizz", "jaycincoo5", 
    "cooknwitkya", "brooklynfrost", "Agent 00", "DeshaeFrost", "NinaDaddyisBack", 
    "girlhefunny1x", "PiperRockelle", "evelynomadera", "CapriSun", "Duke", 
    "vanillamace", "SoLLUMINATI", "ExtraEmily", "summyahmarie", "DannyBans", 
    "Jynxzi", "youngdabo", "PungaxDezz", "Marlon", "thezeddywill", "caseoh_", 
    "imbadkidjay", "xoxvivixox", "shankcomics", "YonnaJay", "ChickletHF", 
    "LightskinMonte", "Quan", "Mastu", "Lacy", "Plaqueboymax", "IShowSpeed", 
    "xQc", "AdinRoss", "zackrawrr", "eliasn97", "Caedrel", "HasanAbi", "JaredFPS"
]
# (All functions like get_trending_youtube_video, etc., are the same as before)
def get_trending_youtube_video(topic):
    """Searches YouTube for a top video about a topic and returns its details."""
    print(f"Searching YouTube for a top video about '{topic}'...")
    try:
        youtube = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
        seven_days_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).isoformat()
        request = Youtube().list(
            part="snippet", q=f"{topic} highlights stream", type="video", order="viewCount",
            maxResults=1, relevanceLanguage="en", publishedAfter=seven_days_ago
        )
        response = request.execute()
        if response.get("items"):
            video = response["items"][0]
            title, description = video["snippet"]["title"], video["snippet"]["description"]
            video_id, video_url = video["id"]["videoId"], f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            print(f"  - Found top video: \"{title}\"")
            return title, description, video_url
        else:
            print(f"  - No relevant YouTube videos found for '{topic}'.")
            return None, None, None
    except HttpError as e:
        print(f"  - An HTTP error {e.resp.status} occurred: {e.content}")
        return None, None, None
    except Exception as e:
        print(f"  - An error occurred fetching from YouTube: {e}")
        return None, None, None

def generate_tweet_from_video(topic_name, title, description, video_url):
    """Uses Gemini to write a tweet about a YouTube video."""
    if not title: return None
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = (f"You are a social media commentator. The following is a top trending YouTube video about '{topic_name}'. Rewrite the title and description into an engaging, short, and exciting tweet. Mention what happened in the video and include the video link at the end. Keep the tweet under 280 characters. Do not just copy the title. Title: \"{title}\"\nDescription: \"{description}\"\nVideo URL: {video_url}")
        print("  - Sending video details to Gemini for tweet generation...")
        ai_response = model.generate_content(prompt)
        print("---\nGenerated tweet content:")
        return ai_response.text.strip()
    except Exception as e:
        print(f"Error generating content with Gemini: {e}")
        return None

def post_tweet(content):
    """Posts a tweet to your timeline."""
    if not content: return
    try:
        # Note: Tweepy v2 uses Bearer Token for v2 endpoints, but API Key/Secret for v1.1 user-context posting.
        # The following uses OAuth 1.0a for posting, which is correct for user-context actions.
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        response = client.create_tweet(text=content)
        print(f"---\nTweet posted successfully! Tweet ID: {response.data['id']}")
    except Exception as e:
        print(f"Error posting tweet: {e}")

if __name__ == "__main__":
    tweet_text = None
    max_retries = 10 
    shuffled_list = random.sample(STREAMER_LIST, len(STREAMER_LIST))
    for i, selected_topic in enumerate(shuffled_list):
        if i >= max_retries:
            print(f"\nStopping after {max_retries} attempts to conserve API quota.")
            break
        print(f"\n--- Attempt {i + 1}/{max_retries} ---")
        title, description, video_url = get_trending_youtube_video(selected_topic)
        if title: 
            tweet_text = generate_tweet_from_video(selected_topic, title, description, video_url)
            break 
        time.sleep(1) 

    if tweet_text:
        post_tweet(tweet_text)
    else:
        print(f"\nCould not find a suitable video to tweet about after {max_retries} attempts.")