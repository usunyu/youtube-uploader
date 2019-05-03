# -*- coding: utf-8 -*-

import sys, os, subprocess, re, json, requests, httplib2
from requests_html import HTMLSession

BILIBILI_API = 'https://www.kanbilibili.com/api/video/'

MIN_THUMBNAIL_SIZE = 10240 # 10 KB

USAGE = '''

    Usage:

        python youtube_uploader.py cailaoban video.mp4 https://www.bilibili.com/video/av38604809 "《哥谭》第二季"

        python youtube_uploader.py <youtube account> <video file> <origin video url> [playlist]

    Account:

        yportkitty, cailaoban, jieshuo

    Option:

        && osascript -e 'tell application (path to frontmost application as text) to display dialog "The script has completed" buttons {"OK"} with icon caution'

'''

def get_youtube_invalid_content_chars():
    return [
        '<',
        '>',
        '"',
        '`',
        "'",
        '\\',
    ]

def get_youtube_invalid_tag_chars():
    return [
        '<',
        '>',
        ',',
        '，',
        '"',
        '`',
        "'",
        "\\",
    ]

def get_browser_headers():
    return {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36'}

CHUNK_SIZE = 1024

def url_download(url, headers=get_browser_headers()):
    try:
        response = requests.get(url, headers=headers, stream=True)
        total_size = int(response.headers['content-length'])
        format = response.headers['Content-Type']
        filename = 'temp'
        if format == 'image/jpeg':
            filename = filename + '.jpg'
        elif format == 'image/png':
            filename = filename + '.png'
        else:
            print('Unknown content type: {}\n'.format(format))
            filename = filename + '.png'
        file = open(filename, 'wb')
        print('Start downloading...\n')
        download_size = 0
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                file.write(chunk)
                # file.flush()
            download_size = download_size + CHUNK_SIZE
            end = '\r'
            if download_size > total_size:
                download_size = total_size
                end = '\r\n'
            print('Download progress: {:.0%}'.format(float(download_size) / total_size), end=end, flush=True),
        file.close()
        print('Download finish!\n')
        return filename
    except:
        print('Url download exception!\n')
        return None

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# https://github.com/youtube/api-samples/blob/master/python/upload_thumbnail.py
#
# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0
To make this sample run you will need to populate the client_secrets.json file
found at:
    {}
with information from the Cloud Console
https://cloud.google.com/console
For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
"""

def get_authenticated_service(secrets_file, credentials_file):
    flow = flow_from_clientsecrets(secrets_file,
                                   scope=YOUTUBE_READ_WRITE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE.format(secrets_file))

    storage = Storage(credentials_file)
    credentials = storage.get()

    if not credentials:
        print('Credentials file not exists!\n')

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))

# Call the API's thumbnails.set method to upload the thumbnail image and
# associate it with the appropriate video.

def upload_thumbnail(secrets_file, credentials_file, youtube_id, thumbnail_file):

    try:
        youtube = get_authenticated_service(secrets_file, credentials_file)
        youtube.thumbnails().set(videoId=youtube_id, media_body=thumbnail_file).execute()
    except HttpError as e:
        print('An HTTP error %d occurred:\n%s\n' % (e.resp.status, e.content))

    print('The custom thumbnail was successfully set.\n')


def upload(account, video_file, video_url, playlist):
    secrets_file = 'secrets/' + account + '.json'
    credentials_file = 'credentials/' + account + '.json'
    # fetch video info
    video_id = re.findall('.*av([0-9]+)', video_url)[0]
    api_url = BILIBILI_API + video_id
    print('Fetching data from ' + api_url + '...\n')
    try:
        response = requests.get(api_url, headers=get_browser_headers())
    except:
        print('Request api exception!\n')
        return
    payload = json.loads(response.text)
    if payload['err'] != None:
        print('Request api error!\n')
        return
    data = payload['data']
    title = data['title']
    description = data['description']
    for invalid_char in get_youtube_invalid_content_chars():
        title = title.replace(invalid_char, '')
        description = description.replace(invalid_char, '')
    thumbnail_url = data['pic']
    print('Fecthed title: ' + title + '\n')
    print('Fetched description: ' + description + '\n')
    # fetch video tags
    html_session = HTMLSession()
    html_response = html_session.get(video_url)
    html_tags = []
    try:
        html_tags = html_response.html.find('#v_tag', first=True).find('.tag')
    except:
        print('Fetch video tags exception!\n')
    tags = None
    for html_tag in html_tags:
        tag_name = html_tag.text
        for invalid_char in get_youtube_invalid_tag_chars():
            tag_name = tag_name.replace(invalid_char, '')
        if tags:
            tags += ', ' + tag_name
        else:
            tags = tag_name
    if tags:
        print('Fetched tags: ' + tags + '\n')
    if not tags:
        tags = 'entertainment'
    # upload video
    upload_command = 'sudo youtube-upload --privacy private --title="{}" --description="{}" --category="{}" --tags="{}" --client-secrets="{}" --credentials-file="{}" --chunksize=1024000'.format(
        title,
        description,
        'Entertainment',
        tags,
        secrets_file,
        credentials_file
    )
    if playlist:
        upload_command += ' --playlist="' + playlist + '"'
    upload_command += ' ' + video_file
    youtube_id = None
    try:
        print('******************************************')
        print('*  Attention! Password may be required!  *')
        print('******************************************')
        output = subprocess.check_output(upload_command, shell=True)
        youtube_id = output.decode("utf-8").strip()
        if 'Enter verification code: ' in youtube_id:
            youtube_id = youtube_id.replace('Enter verification code: ', '')
    except:
        print('Upload video: ' + title + ' exception!\n')
    # download thumbnail if upload video success
    if youtube_id:
        thumbnail_file = None
        try:
            # check image file size
            response = requests.get(thumbnail_url, headers=get_browser_headers())
            image_size = int(response.headers['content-length'])
            if image_size >= MIN_THUMBNAIL_SIZE:
                print('Start download thumbnail...\n')
                thumbnail_file = url_download(thumbnail_url)
            else:
                print('Thumbnail file too small, skip...\n')
        except:
            print('Download thumbnail exception!\n')
        if thumbnail_file:
            try:
                # upload thumbnail
                upload_thumbnail(secrets_file, credentials_file, youtube_id, thumbnail_file)
            except:
                print('Upload thumbnail exception!\n')
            # remove thumbnails
            os.remove(thumbnail_file)


def usage():
    print(USAGE)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        usage()
        sys.exit(1)

    account = sys.argv[1]
    file = sys.argv[2]
    url = sys.argv[3]
    playlist = None
    if len(sys.argv) == 5:
        playlist = sys.argv[4]

    upload(account, file, url, playlist)
