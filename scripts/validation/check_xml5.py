import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

XML_PATH = PROJECT_ROOT / 'experiments/dataset/normalized_rdd2022_india/train/annotations/India_000005.xml'

tree = ET.parse(XML_PATH)
root = tree.getroot()

classes = set()
for obj in root.findall('object'):
    name = obj.find('name').text
    classes.add(name)

print('Classes:', classes)