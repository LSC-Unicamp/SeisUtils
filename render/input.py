import json
from dataclasses import dataclass


@dataclass
class Input:
    n1: int
    n2: int
    n3: int
    filepath: str
    d2: int = 1
    d3: int = 1
    crop_meters: int = 0
    frame: int = 0
    perc: float = 0.0
    border: bool = False
    blur: bool = False
    negative: bool = False
    threshold: float = 0.0
    output: str = ""
    ignore: bool = False
    cineloop: bool = False


def load_input(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    objects_list = []

    for item in data:
        obj = Input(n1=item['n1'],
                    n2=item['n2'],
                    n3=item['n3'],
                    filepath=item['filepath'],
                    d2=item.get('d2', 0),
                    d3=item.get('d3', 0),
                    crop_meters=item.get('crop_meters', 0),
                    frame=item.get('frame', 0),
                    perc=item.get('perc', 0.0),
                    border=item.get('border', False),
                    blur=item.get('blur', False),
                    negative=item.get('negative', False),
                    threshold=item.get('threshold', 0.0),
                    output=item.get('output', ""),
                    ignore=item.get('ignore', False),
                    cineloop=item.get('cineloop', False),
                    )

        objects_list.append(obj)

    return objects_list
