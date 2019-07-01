#!/usr/bin/env python3

from gi.repository import Playerctl, GLib
import subprocess
import screeninfo
import requests
from PIL import Image, ImageDraw
import io
import musicbrainzngs

musicbrainzngs.set_useragent('Background changer', '0.2.1',
                             'https://github.com/s3rius')
manager = Playerctl.PlayerManager()
(WIDTH, HEIGHT) = (1366, 768)
image_path = '/tmp/music_bg.png'
IMAGE_SMOOTH_RATE = 5
for monitor in screeninfo.get_monitors():
    if monitor.height > HEIGHT and monitor.width > WIDTH:
        WIDTH = monitor.width
        HEIGHT = monitor.height


class MetaData(object):
    def __init__(self, artist, album, artUrl):
        self.artist = artist
        self.album = album
        self.artUrl = artUrl
        self.image_bytes = None
        self.update_image()

    def update_image(self):
        if self.artUrl is not None:
            response = requests.get(self.artUrl)
            if not response.ok:
                restore_bg()
                print("Cannot download from google.")
                return
            print("Downloaded image from google.")
            self.image_bytes = io.BytesIO(response.content)
            return
        print("Searchin in musicbrainz")
        try:
            releases = musicbrainzngs.search_releases(
                f'{self.artist} - {self.album}')
            if releases.get('release-count') == 0:
                print("No releases found.")
                restore_bg()
            release_id = releases.get('release-list')[0].get('id')
            image = musicbrainzngs.get_image(release_id, 'front', 500)
            print("Got image from musicbrainz")
            self.image_bytes = io.BytesIO(image)
        except Exception as e:
            print(f"Can't get image from musicbrainz. Beacuse : {e}")
        return


def interpolate(f_co, t_co, interval):
    det_co = [(t - f) / interval for f, t in zip(f_co, t_co)]
    for i in range(interval):
        yield [round(f + det * i) for f, det in zip(f_co, det_co)]


def update_bg(meta: MetaData):
    if meta.image_bytes is None:
        restore_bg()
    try:
        cover = Image.open(meta.image_bytes)
        #  cover.save(image_path)
        gradient = Image.new('RGBA', (WIDTH, HEIGHT), color=0)
        draw = ImageDraw.Draw(gradient)
        pixels = cover.getcolors(cover.height * cover.width)
        most_frequent_pixel = pixels[0]
        min_frequent_pixel = pixels[0]
        for count, colour in pixels:
            if count > most_frequent_pixel[0]:
                most_frequent_pixel = (count, colour)
            if count <= min_frequent_pixel[0]:
                min_frequent_pixel = (count, colour)
        big_cover_size = (cover.height * IMAGE_SMOOTH_RATE,
                          cover.width * IMAGE_SMOOTH_RATE)
        cover_mask = Image.new('L', big_cover_size, 0)
        mask_drawer = ImageDraw.Draw(cover_mask)
        mask_drawer.ellipse((0, 0) + big_cover_size, fill=255)
        cover_mask = cover_mask.resize(cover.size, Image.ANTIALIAS)
        cover.putalpha(cover_mask)
        for i, color in enumerate(
                interpolate(most_frequent_pixel[1], min_frequent_pixel[1],
                            WIDTH * 2)):
            draw.line([(i, 0), (0, i)], tuple(color), width=1)
        gradient.paste(cover, ((WIDTH - cover.width) // 2,
                               (HEIGHT - cover.height) // 2),
                       mask=cover_mask)
        gradient.save(image_path)
        subprocess.Popen(['feh', '--bg-center', image_path],
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    except Exception:
        restore_bg()


def on_play(player, status, manager):
    meta = MetaData(player.print_metadata_prop("xesam:artist"),
                    player.print_metadata_prop("xesam:album"),
                    player.print_metadata_prop("mpris:artUrl"))
    update_bg(meta)


def restore_bg():
    try:
        subprocess.Popen(["nitrogen", "--restore"],
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    except Exception as e:
        print(f"Exception found: {e}")


def on_pause(player, status, manager):
    restore_bg()


def on_metadata(player, metadata, manager):
    meta = MetaData(player.print_metadata_prop("xesam:artist"),
                    player.print_metadata_prop("xesam:album"),
                    player.print_metadata_prop("mpris:artUrl"))
    update_bg(meta)


def init_player(name):
    # choose if you want to manage the player based on the name

    player = Playerctl.Player.new_from_name(name)
    player.connect('playback-status::playing', on_play, manager)
    player.connect('playback-status::paused', on_pause, manager)
    player.connect('playback-status::stopped', on_pause, manager)
    player.connect('metadata', on_metadata, manager)
    manager.manage_player(player)


def on_name_appeared(manager, name):
    init_player(name)


def on_player_vanished(manager, player):
    restore_bg()


manager.connect('name-appeared', on_name_appeared)
manager.connect('player-vanished', on_player_vanished)

for name in manager.props.player_names:
    init_player(name)

main = GLib.MainLoop()
main.run()
