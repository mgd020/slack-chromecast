import re
import time

import pychromecast
import pychromecast.controllers.youtube as youtube
from slackclient import SlackClient


YOUTUBE_VIDEO_ID_RE = re.compile(r"(?:(?<=(?:v|V)/)|(?<=be/)|(?<=(?:\?|\&)v=)|(?<=embed/))([\w-]+)")


def find_chromecasts(names=None, cast_type=None):
    ccs = pychromecast.get_chromecasts()
    if names:
        ccs = filter(lambda cc: cc.name in names, ccs)
    if cast_type:
        ccs = filter(lambda cc: cc.cast_type == cast_type, ccs)
    return list(ccs)


def get_youtube_chromecast(name=None):
    chromecast = find_chromecasts(names=[name] if name else None, cast_type=pychromecast.CAST_TYPE_CHROMECAST)[0]
    chromecast.youtube_controller = youtube.YouTubeController()
    chromecast.register_handler(chromecast.youtube_controller)
    return chromecast


def handle_video_id(chromecast, video_id):
    print("Handle", video_id)
    chromecast.youtube_controller.add_to_queue(video_id)
    chromecast.media_controller.play()


def main(oath_access_token, chromecast_name=None):
    chromecast = get_youtube_chromecast(chromecast_name)
    print("Found", chromecast)
    slack_client = SlackClient(oath_access_token)
    assert slack_client.api_call("auth.test").get("ok") is True
    assert slack_client.rtm_connect(with_team_state=False)
    while True:
        for event in slack_client.rtm_read():
            if event["type"] == "message" and "previous_message" not in event:
                for video_id in YOUTUBE_VIDEO_ID_RE.findall(event["text"]):
                    handle_video_id(chromecast, video_id)
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Queue youtube songs from slack channels")
    parser.add_argument("--token", required=True, dest="oath_access_token", help="Bot User OAuth Access Token")
    parser.add_argument("--cast", dest="chromecast_name", help="Name of specific chromecast")
    kwargs = vars(parser.parse_args())
    try:
        main(**kwargs)
    except KeyboardInterrupt:
        pass
