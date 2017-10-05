import errno
import pywal
import shutil
from random import shuffle
from os.path import realpath
from os import symlink, remove, path
from subprocess import Popen, call
from . import color, sample, config, files


def create_theme(filepath):
    filename = filepath.split("/").pop().replace(" ", "_")
    shutil.copy2(filepath, path.join(config.WALL_DIR, filename))
    image = pywal.image.get(path.join(config.WALL_DIR, filename))
    colors = pywal.colors.get(image, config.WALL_DIR)
    pywal.export.color(colors,
                       "xresources",
                       path.join(config.XRES_DIR, (filename + ".Xres")))
    color_list = [colors['colors']['color%s' % i] for i in range(16)]
    sample.create_sample(color_list,
                         f=path.join(config.SAMPLE_DIR,
                                     (filename + '.sample.png')))


def set_theme(filename, cs_file, restore=False):
    if(path.join(config.WALL_DIR, filename)):
        if(not restore):
            color.execute_gcolorchange(cs_file)
            pywal.reload.gtk()
            pywal.reload.i3()
            pywal.reload.polybar()

        pywal.wallpaper.change(path.join(config.WALL_DIR, filename))
        image = pywal.image.get(path.join(config.WALL_DIR, cs_file))
        colors = pywal.colors.get(image, config.WALL_DIR)
        pywal.sequences.send(colors, False, config.WALL_DIR)
        pywal.export.color(colors, 'css',
                           path.join(config.WALL_DIR, 'current.css'))
        pywal.export.color(colors, 'shell',
                           path.join(config.WALL_DIR, 'current.sh'))

        init_file = open(path.join(config.WALL_DIR, 'wp_init.sh'), 'w')
        init_file.writelines(['#!/bin/bash\n', 'wpg -r -s ' +
                              filename + ' ' + cs_file])
        init_file.close()
        Popen(['chmod', '+x', path.join(config.WALL_DIR, 'wp_init.sh')])
        call(['xrdb', '-merge',
              path.join(config.XRES_DIR, (cs_file + '.Xres'))])
        call(['xrdb', '-merge', path.join(config.HOME, '.Xresources')])
        try:
            if config.wpgtk.getboolean('execute_cmd'):
                Popen(config.wpgtk['command'].split(' '))
            symlink(path.join(config.WALL_DIR, filename),
                    path.join(config.WALL_DIR, ".current"))
        except Exception as e:
            if e.errno == errno.EEXIST:
                remove(path.join(config.WALL_DIR, ".current"))
                symlink(path.join(config.WALL_DIR, filename),
                        path.join(config.WALL_DIR, ".current"))
            else:
                raise e
    else:
        print("no such file, available files:")
        files.show_files()


def delete_theme(filename):
    cache_file = path.join(config.WALL_DIR, filename)
    remove(path.join(config.WALL_DIR, filename))
    remove(path.join(config.SAMPLE_DIR, (filename + '.sample.png')))
    remove(path.join(config.XRES_DIR, (filename + '.Xres')))
    remove(path.join(config.SCHEME_DIR,
           (cache_file.replace('/', '_').replace('.', '_') + ".json")))


def get_current(show=False):
    image = realpath(path.join(config.WALL_DIR, '.current')).split('/').pop()
    if show:
        print(image)
    return image


def shuffle_colors(filename):
    try:
        colors = color.get_color_list(filename)
        shuffled_colors = colors[1:7]
        shuffle(shuffled_colors)
        colors = colors[:1] + shuffled_colors + colors[7:]
        sample.create_sample(colors, f=path.join(config.SAMPLE_DIR,
                             filename + '.sample.png'))
        color.write_colors(filename, colors)
    except IOError as e:
        print('ERR:: file not available')


def auto_adjust_colors(filename):
    try:
        color_list = color.get_color_list(filename)
        color8 = color_list[0:1][0]
        if not config.wpgtk.getboolean('light_theme'):
            color8 = [color.add_brightness(color8, 18)]
            color_list = color_list[:8:]
            color_list += color8
            color_list += [color.add_brightness(x, 50)
                           for x in color_list[1:8:]]
        else:
            color8 = [color.reduce_brightness(color8, 18)]
            color_list = color_list[:8:]
            color_list += color8
            color_list += [color.reduce_brightness(x, 50)
                           for x in color_list[1:8:]]
        sample.create_sample(color_list,
                             f=path.join(config.SAMPLE_DIR,
                                         (filename + '.sample.png')))
        color.write_colors(filename, color_list)
    except IOError:
        print('ERR:: file not available')