from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from tqdm import tqdm
import time
import requests
# import numpy as np
# from keras.models import load_model
from threading import Thread

import json

import random
from datetime import date

import logging
from pprint import pprint

from dotenv import load_dotenv
import os

import vlc

load_dotenv()


ngrok_url = os.environ.get("NGROK_URL")


# model = load_model("../network2.h5")


# def make_prediction(brain_waves):
#     prediction = model.predict([brain_waves])
#     return prediction


# def classify_eeg_sentiment(prediction):
#     print(prediction)
#     [pred_val] = prediction
#     if pred_val < 0.25:
#         return 0
#     elif 0.25 < pred_val < 0.50:
#         return 1
#     elif 0.50 < pred_val < 0.75:
#         return 2
    # return 3


def get_random_search_term():
    chars = 'abcdefghijklmnopqrstuvwxyz'
    picked_char = random.choice(chars)
    case = random.randint(1, 2)
    if case == 1:
        search_term = f"{picked_char}%"
    elif case == 2:
        search_term = f"%{picked_char}%"

    return search_term


def get_random_song(sp: Spotify):
    while True:
        search_term = get_random_search_term()
        random_idx = random.randint(0, 200)

        logging.info(
            f"Attempting to search songs with search_term={search_term} and offset={random_idx}...")
        search_results = sp.search(
            q=search_term, limit=50, offset=random_idx, type="track", market="US")
        logging.info(
            f"Successfully found search results with search_term={search_term}!")

        tracks = search_results["tracks"]["items"]
        random.shuffle(tracks)

        logging.info(
            f"Attempting to find songs in search results with preview_url...")
        picked_track = None
        for track in tracks:
            if track["preview_url"] is not None:
                logging.info(f"Found preview url for track ({track['name']})!")
                picked_track = track
                break
            else:
                logging.info(
                    f"No preview url for track ({track['name']})... skipping track")

        if picked_track is not None:
            break
        else:
            logging.info(
                f"Failed to find songs in search results with preview_url... Will attempt with new search term")
            continue

    return picked_track


def get_track_info(sp: Spotify, track: dict):
    name = track["name"]
    album = track["album"]["name"]
    images: list = track["album"]["images"]
    track_url = track["external_urls"]["spotify"]
    preview_url = track["preview_url"]
    uri = track["uri"]

    artists = []
    artists_ids = []
    for artist in track["artists"]:
        artists.append(artist["name"])
        artists_ids.append(artist["uri"])

    genres = []
    for id in artists_ids:
        artist = sp.artist(id)
        for genre in artist["genres"]:
            genres.append(genre)
    genres = sorted(list(set(genres)))

    track_info = {
        "name": name,
        "artists": artists,
        "album": album,
        "images": images,
        "genres": genres,
        "track_url": track_url,
        "preview_url": preview_url,
        "uri": uri
    }

    return track_info


def get_recommendations(sp: Spotify, tracks: list):
    recommendations = sp.recommendations(
        seed_tracks=tracks, limit=len(tracks)*2, country="US")
    return recommendations


def create_playlist(sp: Spotify, tracks: list, playlist_name: str):
    logging.info(f"Attempting to create playlist with name {playlist_name}...")
    playlist = sp.user_playlist_create(
        user="nqltssfvzdor050r1fcai466e",
        name=playlist_name,
        public=True,
        description=f"Created using CTRL Freaks' EEG device, on {date.today()}"
    )
    logging.info(f"Created playlist with name {playlist_name}!")

    playlist_id = playlist["id"]

    logging.info(f"Attempting to add tracks to playlist {playlist_name}...")
    sp.playlist_add_items(playlist_id=playlist_id, items=tracks)
    logging.info(f"Successfully added tracks to playlist {playlist_name}!")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    url = "https://accounts.spotify.com/api/token"
    code = "your_authorization_code"
    myurl = "your_redirect_uri"
    mysecret = "your_client_secret"
    myid = "your_client_id"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": myurl,
        "client_secret": mysecret,
        "client_id": myid
    }

    logging.info("Attempting to create Spotify API client...")
    sp = Spotify(client_credentials_manager=SpotifyClientCredentials())
    logging.info("Successfully created Spotify API client!")

    positive = []
    negative = []
    neutral = []
    for _ in range(10):
        logging.info("Attempting to get random track...")
        track = get_random_song(sp)
        logging.info(f"Found random track ({track['name']})!")

        logging.info("Attempting to get track info...")
        track_info = get_track_info(sp, track)
        logging.info("Successfully got track info! Displaying below:")
        pprint(track_info)

        # play the track preview
        logging.info("PLAYING TRACK")
        p = vlc.MediaPlayer(track_info["preview_url"])
        p.play()
        logging.info("DONE PLAYING TRACK")

        # hit the api x times for eeg data
        brain_waves = []
        for i in tqdm(range(14)):
            time.sleep(2)
            response = requests.get(ngrok_url + "/eeg_data")
            raw_data = response.json()
            data = raw_data["eeg_asic"]
            brain_waves.append([data['delta'], data['theta'], data['low-alpha'], data['high-alpha'], data['low-beta'],
                               data["high-beta"], data["low-gamma"], data["mid-gamma"], raw_data["attention"], raw_data["meditation"]])

        # classify eeg data
        # prediction = make_prediction(brain_waves)
        sentiment = int(requests.post(
            ngrok_url + "/classify-brain-waves", json={"brainwaves": brain_waves}).content)
        print(sentiment)
        # sentiment = classify_eeg_sentiment(prediction)

        # take input on sentiment
        # while True:
        #     inp = input("How do you feel about the track? Positive (+), Negative (-), Netural (/)\nEnter on the above options: ").strip().lower()
        #     if inp not in ["+", "-", "/"]:
        #         print("Invalid option selected. Please pick (+), (-), or (/) only. Without the brackets.")
        #     else:
        #         break

        # TODO: use labels from classifier
        # add input to appropriate list
        if sentiment == 0:
            positive.append(track_info["uri"])
        elif sentiment == 1:
            positive.append(track_info["uri"])
        elif sentiment == 2:
            neutral.append(track_info["uri"])
        elif sentiment == 3:
            negative.append(track_info["uri"])

        if len(positive) >= 5:
            break

    # create list of shortlisted tracks
    if len(positive) < 5:
        logging.info(
            f"Not enough positve tracks found ({len(positive)})... appending neutral tracks ({len(neutral)}) also to shortlist!")
        shortlisted_tracks = positive + neutral
    else:
        logging.info(f"Adding positve tracks ({len(positive)}) to shortlist!")
        shortlisted_tracks = positive

    pprint(shortlisted_tracks)

    # TODO: generate recommendations based on seed track
    logging.info(f"Attempting to generate recommendations...")
    sp_user_session = Spotify(
        auth_manager=SpotifyOAuth(
            scope="playlist-modify-public",
            cache_path="token.txt"
        )
    )

    recommendations = get_recommendations(sp_user_session, shortlisted_tracks)

    # logging.info(f"Successfully generated recommendations!")
    with open("./junk.json", "w") as file_obj:
        file_obj.write(json.dumps(recommendations, indent=4))

    # create_playlist(sp, shortlisted_tracks, "EEGTestPlaylist1")


if __name__ == '__main__':
    main()

"""
TODOs:

picker for market/country
    https://developer.spotify.com/documentation/web-api/reference/get-available-markets

create function for recommendations
    https://developer.spotify.com/documentation/web-api/reference/get-recommendations
"""
