import xml.etree.ElementTree as ET

tree = ET.parse('C:/Users/viraj/Code_files/Github/RoadGuard AI/experiments/dataset/normalized_rdd2022_india/train/annotations/India_000005.xml')
root = tree.getroot()

classes = set()
for obj in root.findall('object'):
    name = obj.find('name').text
    classes.add(name)

print('Classes:', classes)