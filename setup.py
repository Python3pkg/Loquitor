import os

from setuptools import setup
config_path = os.path.join(os.path.expanduser("~"), ".loquitor")
py_modules = ['bot', 'skeleton']
setup(name='loquitor',
      version='1.0.3',
      description='Chatbot for Stack Overflow',
      author='Ralph Embree',
      author_email='ralph.embree@brominator.org',
      url='https://github.com/ralphembree/Loquitor',
      packages=['Loquitor', 'Loquitor.scripts'],
      install_requires=['BingTranslator', 'feedparser', 'ChatExchange'],
      dependency_links=['https://github.com/ByteCommander/ChatExchange6/tarball/master#egg=ChatExchange-1.0'],
      scripts=['bin/loquitor'],
      data_files=[(config_path, ['Loquitor/scripts/SUBSTITUTIONS.txt'])],
)
