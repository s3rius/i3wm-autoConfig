#!/usr/bin/env python3
from gi.repository import Playerctl, GLib
import subprocess
import screeninfo
import requests
from PIL import Image, ImageDraw, ImageFilter
import io
import musicbrainzngs
import math
import random
import sounddevice as sd
import numpy as np
musicbrainzngs.set_useragent('Background changer', '0.2.1',
                             'https://github.com/s3rius')
manager = Playerctl.PlayerManager()
(WIDTH, HEIGHT) = (0, 0)
image_path = '/tmp/music_bg.png'
equalizer_path = "/tmp/eq_bg.png"
IMAGE_SMOOTH_RATE = 5

samplerate = sd.query_devices(None, 'input')['default_samplerate']
print(f"samplerate = {samplerate}")
low, high = (100, 2000)
delta_f = (high - low) / 40

fftsize = math.ceil(samplerate / delta_f)

low_bin = math.floor(low / delta_f)

current_image = None
distances = [[0 for i in range(WIDTH)] for i in range(HEIGHT)]

for y in range(HEIGHT):
    for x in range(WIDTH):
        # Find the distance to the center
        distanceToCenter = math.sqrt((x - WIDTH / 2)**2 + (y - HEIGHT / 2)**2)

        # Make it on a scale from 0 to 1
        distanceToCenter = distanceToCenter / (math.sqrt(2) * WIDTH / 2)
        distances[y][x] = distanceToCenter

print("Distances calculated")

#  class FehViewer(ImageShow.UnixViewer):
#
#  def show_file(self, filename, **options):
#  os.system('feh --bg-center %s' % filename)
#  return 1

#  ImageShow.register(FehViewer, order=-1)


def music_callback(indata, frames, time, status):
    #  print("listening")
    if any(indata):
        magnitude = np.abs(np.fft.rfft(indata[:, 0], n=fftsize))
        magnitude *= 10 / fftsize
        global current_image
        local_img = current_image.copy()
        drawer = ImageDraw.Draw(local_img)
        for i, el in enumerate(magnitude):
            print(f"i({i}), el({el * 10000})")
            drawer.line((i * 2, HEIGHT, i * 2, HEIGHT - (el * 100)),
                        fill=200,
                        width=2)
        del drawer
        local_img.save(equalizer_path)
        subprocess.Popen(['feh', '--bg-center', equalizer_path],
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)


stream = None


class MetaData(object):
    def __init__(self, artist, album, artUrl):
        self.artist = artist
        self.album = album
        self.artUrl = artUrl
        self.image_bytes = None
        self.update_image()

    def update_image(self):
        if self.artUrl is not None:
            print("Started loading...")
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


def draw_linear_gradient(image, from_color, to_color, inversion):
    print("Generating linear gradient")
    if inversion:
        tmp = from_color
        from_color = to_color
        to_color = tmp
    drawer = ImageDraw.Draw(image)
    for i, color in enumerate(interpolate(from_color, to_color, WIDTH * 2)):
        drawer.line([(i, 0), (0, i)], tuple(color), width=1)


def draw_radial_gradient(image: Image, innerColor, outerColor, inversion):
    print("Generating radial gradient.")
    if inversion:
        tmp = innerColor
        innerColor = outerColor
        outerColor = tmp
    imgsize = (image.width, image.height)
    for y in range(imgsize[1]):
        for x in range(imgsize[0]):
            distanceToCenter = distances[y][x]
            # Calculate r, g, and b values
            r = outerColor[0] * distanceToCenter + innerColor[0] * (
                1 - distanceToCenter)
            g = outerColor[1] * distanceToCenter + innerColor[1] * (
                1 - distanceToCenter)
            b = outerColor[2] * distanceToCenter + innerColor[2] * (
                1 - distanceToCenter)

            image.putpixel((x, y), (int(r), int(g), int(b)))


def genearate_gradinent(width, height, from_color, to_color):
    gradient = Image.new('RGB', (width, height))
    inversion = random.randint(0, 1) == 0
    draw_radial_gradient(gradient, from_color, to_color, inversion)
    #  draw_linear_gradient(gradient, from_color, to_color, inversion)
    return gradient


def scaled_blur(metadata: MetaData):
    back = Image.open(metadata.image_bytes)
    resize_rate = math.ceil(WIDTH / back.width)
    print(f"resize rate: {WIDTH}/{back.width}={resize_rate}")
    resized = back.resize(
        (back.width * resize_rate, back.height * resize_rate),
        Image.ANTIALIAS).filter(ImageFilter.GaussianBlur(8))
    resized = resized.crop(
        ((resized.width - WIDTH) / 2, (resized.height - HEIGHT) / 2,
         (resized.width + WIDTH) / 2, (resized.height + HEIGHT) / 2))
    return resized


def update_bg(meta: MetaData):
    if meta.image_bytes is None:
        restore_bg()
    try:
        global WIDTH
        global HEIGHT
        WIDTH = 0
        HEIGHT = 0
        for monitor in screeninfo.get_monitors():
            if monitor.height >= HEIGHT and monitor.width >= WIDTH:
                WIDTH = monitor.width
                HEIGHT = monitor.height
        print(f"Biggest screen size is {WIDTH}x{HEIGHT}")
        cover = Image.open(meta.image_bytes)
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
        gradient = scaled_blur(meta)
        gradient.paste(cover, ((WIDTH - cover.width) // 2,
                               (HEIGHT - cover.height) // 2),
                       mask=cover_mask)
        global current_image
        current_image = gradient
        gradient.save(image_path)
        subprocess.Popen(['feh', '--bg-center', image_path],
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE)
        #  global stream
        #  stream = sd.InputStream(device=None,
        #  channels=1,
        #  callback=music_callback,
        #  blocksize=int(samplerate * 50 / 1000),
        #  samplerate=samplerate)
        #  stream.start()
    except Exception as e:
        print(f"We're fucked up, sir. Exception: {e}")
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
        #  stream.close()
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
