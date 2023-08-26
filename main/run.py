    @staticmethod
    def scrape_playlists_for_genres(user_id=None,limit=50, offset=0, access_token=SAH.current_access_token()):
        playlist_ids = ItemInfo.get_users_playlists(user_id)
        tracks = []

        for playlist_id in playlist_ids:
            response = requests.get(
                playlist_items_url.format(playlist_id=playlist_id),
                headers={
                    'Authorization': f"Bearer {access_token}"
                },
                params={
                    'fields': 'items(track(id,name,artists(id,name)))',
                    'limit': limit,
                    'offset': offset
                }
            )

            if response.status_code == 200:
                logger_recommendations.log_message('info', f"Successfully retrieved playlist's items {response.json}")
                json_resp = response.json()

                
                for item in json_resp['items']:
                    artist_id = []
                    if not item['track']:
                        logger_recommendations.log_message('info', f"Item's track is None, prev item: {track_info}")
                        continue
                    
                    for artist in item['track']['artists']:
                        artist_id.append(artist['id'])

                    track_info = {
                        'track_id': item['track']['id'],
                        'artists_ids': artist_id
                    }

                    # Store the track information in the tracks dictionary
                    tracks.append(track_info)

        # Now that we have the artist ids and track ids, we can get the genres
        for track_id, track_info in tracks.items():
            if track_id in tracks_genres_data:
                track_genres = tracks_genres_data[track_id]
            else:
                artist_ids_concat = ','.join(track_info['artists_ids'])
                track_genres = set(ItemInfo.get_artists_genres(artist_ids_concat))
                tracks_genres_data[track_id] = list(track_genres)

            for genre in track_genres:
                if genre in user_genres_data:
                    if 'tracks' not in user_genres_data[genre]:
                        user_genres_data[genre]['tracks'] = []
                    if track_id not in user_genres_data[genre]['tracks']:
                        user_genres_data[genre]['tracks'].append(track_id)
                else:
                    user_genres_data[genre] = {'tracks': [track_id]}

            # Update the artists_genres_data
            for artist_id in track_info['artists_ids']:
                if artist_id in artists_genres_data:
                    artist_genres = artists_genres_data[artist_id]
                else:
                    artist_genres = set(ItemInfo.get_artists_genres(artist_id))
                    artists_genres_data[artist_id] = list(artist_genres)
                    # To not cross rate limit
                    
                    time.sleep(0.5)
                for genre in artist_genres:
                    if genre in user_genres_data:
                        if 'artists' not in user_genres_data[genre]:
                            user_genres_data[genre]['artists'] = []
                        if artist_id not in user_genres_data[genre]['artists']:
                            user_genres_data[genre]['artists'].append(artist_id)
                    else:
                        user_genres_data[genre] = {'artists': [artist_id]}

        # Update the JSON files with the new data
        dump_file(tracks_genres_data_file, tracks_genres_data)
        dump_file(artists_genres_data_file, artists_genres_data)
        dump_file(user_genres_data_file, user_genres_data)