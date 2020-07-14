from setuptools import setup


setup(name='pyaisnmea',
      version='2020.7',
      description='a Python 3 AIS NMEA 0183 decoder',
      author='Thomas W Whittam',
      url='https://github.com/tww-software/py_ais_nmea',
      license='MIT',
      packages=['pyaisnmea', 'pyaisnmea.messages', 'pyaisnmea.gui'],
      install_requires=['tkinter'],
      include_package_data=True,
      zip_safe=False
)

