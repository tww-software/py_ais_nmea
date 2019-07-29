"""
rotate an image 360 degrees

Note:
    this require imagemagick to be installed
"""

import subprocess

def rotate_image(imagepath, angle):
    """
    rotate an image
    """
    try:
        subprocess.run(['convert', imagepath, '-distort', 'SRT',
                       str(angle), str(angle) + '.png'])
    except Exception as err:
        print('unable to rotate to {}, error - {}'.format(angle, str(err)))


if __name__ == '__main__':
    for angle in range(1, 360):
        print('rotating {}'.format(angle))
        rotate_image('0.png', angle)
