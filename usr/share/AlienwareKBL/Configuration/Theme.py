#!/usr/bin/python3
#

#  Copyright (C) 2014-2015, 2017  Rafael Senties Martinelli <rafael@senties-martinelli.com>
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License 3 as published by
#   the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA.

import os
import sys
from copy import copy
from traceback import format_exc

# Local imports
from .Paths import Paths
sys.path.append("../")
from Engine.Area import Area
from Engine.Zone import Zone

AVAILABLE_THEMES = {}

def get_theme_by_name(name):
    return AVAILABLE_THEMES[name]

def LOAD_profiles(computer, theme_path):

    global AVAILABLE_THEMES
    AVAILABLE_THEMES = {}

    # Load the existing AVAILABLE_THEMES
    #
    if not os.path.exists(theme_path):
        os.mkdir(theme_path)
    else:
        files = os.listdir(theme_path)

        for file in files:
            if file.endswith('.cfg'):
                LOAD_profile(computer, theme_path + file)

    # Add the default profile
    #
    if len(AVAILABLE_THEMES.keys()) <= 0:
        CREATE_default_profile(computer, theme_path)


def LOAD_profile(computer, path):
    new_config = Theme(computer)
    new_config.path = path
    new_config.load(path)


def CREATE_default_profile(computer, theme_path):
    config = Theme(computer)
    config.create_profile('Default', theme_path + 'Default.cfg')
    config.save()


def GET_last_configuration():
    max = None
    profile_numb = 0
    profile_name = None

    for num, key in enumerate(sorted(AVAILABLE_THEMES.keys())):

        profile = AVAILABLE_THEMES[key]
        profile.update_time()

        if max is None or profile.time > max:
            max = profile.time
            profile_numb = num
            profile_name = profile.name

    return profile_numb, profile_name

class Theme:

    def __init__(self, computer):

        self.name = ''
        self.time = None
        
        self._speed = 65280
        self._areas = {}
        self._computer = copy(computer)

    def create_profile(self, name, path, speed=False):
        self.name = name
        self.set_speed(speed)
        self.path = path

        for region in self._computer.get_regions():
            
            area = Area()
            area.init_from_region(region)
            
            zone = Zone(mode=self._computer.DEFAULT_MODE, 
                        left_color=self._computer.DEFAULT_COLOR, 
                        right_color=self._computer.DEFAULT_COLOR)
                                 
            area.add_zone(zone)
            self.add_area(area)

        AVAILABLE_THEMES[self.name] = self

    def get_areas(self):
        return [area for area in self._areas.values()]

    def get_area_by_name(self, area_name):
        return self._areas[area_name]

    def add_area(self, area):
        if not area.name in self._areas.keys():
            self._areas[area.name] = area
        else:
            print("Warning Theme: Duplicated area `{}`, `{}`".format(area.name, self._areas.keys()))

    def save(self):
        with open(self.path, encoding='utf-8', mode='wt') as f:
            f.write('name={0}\n'.format(self.name))
            f.write('computer={0}\n'.format(self._computer.NAME))
            f.write('speed={0}\n\n\n'.format(self._speed))

            for key in sorted(self._areas.keys()):
                area = self._areas[key]

                f.write('area={0}\n'.format(area.name))
                for zone in area:
                    f.write('mode={0}\n'.format(zone.get_mode()))
                    f.write('left_color={0}\n'.format(zone.get_left_color()))
                    f.write('right_color={0}\n'.format(zone.get_right_color()))
                f.write('\n')

        self.update_time()

    def load(self, path):

        lines = []
        with open(path, encoding='utf-8', mode='rt') as f:
            lines = f.readlines()

        area_found, left_color, right_color, mode, = False, False, False, False

        imported_areas = []
        supported_region_names = self._computer.get_supported_regions_names()

        # Parse the configuration file
        #
        for line in lines:
            if line.strip():
                variables = line.strip().split('=')

                if len(variables) == 2:

                    var_name = variables[0]
                    var_arg = variables[1]

                    if var_name == 'name':
                        if var_arg == '':
                            name = os.path.basename(path)
                        else:
                            name = var_arg

                        if name.endswith('.cfg'):
                            name = name[:-4]

                        self.name = name

                    elif var_name == 'speed':
                        self.set_speed(var_arg)

                    elif var_name == 'area':
                        area_name = var_arg

                        if area_name in supported_region_names:
                            area_found=True
                            imported_areas.append(area_name)
                            region = self._computer.get_region_by_name(area_name)
                            area = Area()
                            area.init_from_region(region)                            
                            self.add_area(area)
                        else:
                            area_found=False
                            print("Warning Theme: area name `{}` not listed on computer regions.".format(area_name))

                    elif var_name in ('type','mode'):
                        mode = var_arg
                        if mode not in ('fixed', 'morph', 'blink'):
                            mode = self._computer.DEFAULT_MODE
                            print('Warning Theme: wrong mode=`{}` when importing theme. Using default mode.')
                        
                        

                    elif var_name in ('color','color1','left_color'):
                        color1 = var_arg

                    elif var_name in ('color2','right_color'):
                        color2 = var_arg

                    if area_found and left_color and right_color and mode:
                        
                        zone=Zone(mode=mode, left_color=left_color, right_color=right_color)
                        area.add_zone(zone)

                        left_color, right_color, mode = False, False, False

        # Add areas in case they be missing
        #
        for area_name in supported_region_names:
            if area_name not in imported_areas:

                region = self._computer.get_region_by_name(area_name)
                area = Area()
                area.init_from_region(region)

                zone = Zone(mode=self._computer.DEFAULT_MODE, 
                            left_color=self._computer.DEFAULT_COLOR, 
                            right_color=self._computer.DEFAULT_COLOR)
                area.add_zone(zone)
                self.add_area(area)
                print("Warning Theme: missing area `{}` on theme `{}`.".format(area_name, self.name))

        #
        # Add the configuration
        #
        AVAILABLE_THEMES[self.name] = self

    def get_speed(self):
        return self._speed

    def set_speed(self, speed):
        try:
            speed = int(speed)
            if speed >= 256 * 255:
                self._speed = 256 * 255
            elif speed <= 256:
                self._speed = 256
            else:
                self._speed = speed

        except Exception as e:
            self._speed = 1

            print("Warning Theme: error setting the speed.")
            print(format_exc())

    def modify_zone(self, zone, column, left_color, right_color, mode):
        zone = self._areas[zone.name][column]
        zone.color1 = color1
        zone.color2 = color2
        zone.mode = mode

    def delete_zone(self, zone, column):
        try:
            area = self._areas[zone.name]
            area.remove_zone(column)

        except Exception as e:
            print('Warning Theme: column `{}`'.format(column))
            print(format_exc())

    def update_time(self):
        if os.path.exists(self.path):
            self.time = os.path.getmtime(self.path)
