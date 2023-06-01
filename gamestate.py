import pyarrow.parquet as pq
import json
from collections import Counter

class ProcessGameState:
    def __init__(self, path): # specify file path upon initialization
        self.path = path
        self.data = self.create_data()
        self.size = len(self.data)

    def create_data(self): # creates pandas dataframe as class attribute ; (self.data)
        data = pq.ParquetFile(self.path)
        print(f"Data at {self.path} loaded")
        table = data.read()
        data_frame = table.to_pandas()
        return data_frame

    def within_boundary(self, boundary_vertices=[(-1735, 250), (-2806, 742), (-2472, 1233), (-1565, 580)]):
        def is_within_boundary(point, vertices):
            def dot_product(point1, point2, pointT):
                return ((point2[0] - point1[0]) * (pointT[0] - point1[0])) + ((point2[1] - point1[1]) * (pointT[1] - point1[1]))

            return not any(dot_product(v, v_next, point) <= 0 for v, v_next in zip(vertices, vertices[1:] + vertices[:1]))

        filtered_data = self.data[
            (self.data['z'] >= 285) & (self.data['z'] <= 421) &
            self.data.apply(lambda row: is_within_boundary((row['x'], row['y']), boundary_vertices), axis=1)
        ]
        return filtered_data
    
    def filter_data_by_bool(self, column : bool, equal_value=None, not_equal_value=None):
        if equal_value: # filter by exact matches
            filtered_data = self.data[
                (self.data[column] == equal_value)
            ]
            return filtered_data
        if not_equal_value: # filter by exact non-matches
            filtered_data = self.data[
                (self.data[column] != not_equal_value)
            ]
            return filtered_data

    def filter_data_by_int(self, column : int, minimum_value=-100000000, maximum_value=100000000, equal_value=None, not_equal_value=None):
        if equal_value: # filter by exact matches
            filtered_data = self.data[
                (self.data[column] == equal_value)
            ]
            return filtered_data
        if not_equal_value: # filter by exact non-matches within minimum and maximum
            filtered_data = self.data[
                (self.data[column] != not_equal_value) & (self.data[column] >= minimum_value) & (self.data[column] <= maximum_value)
            ]
            return filtered_data
        if True: # filter by within minimum and maximum
            filtered_data = self.data[
                (self.data[column] >= minimum_value) & (self.data[column] <= maximum_value) 
            ]
            return filtered_data

    def filter_data_by_str(self, column : str, equal_value=None, not_equal_value=None):
        if equal_value: # filter by exact matches
            filtered_data = self.data[
                (self.data[column] == equal_value)
            ]
            return filtered_data
        if not_equal_value: # filter by exact non-matches
            filtered_data = self.data[
                (self.data[column] != not_equal_value)
            ]
            return filtered_data

    def extract_weapons_classes(self, data_type : str):

        weapon_classes = list()
        for inventory in self.data['inventory']:
            try:
                d = dict(enumerate(inventory.flatten(), 1))
                weapon_classes.append(d[1]['weapon_class'])
            except:
                pass

        if data_type == "counter":
            return Counter(weapon_classes)
        if data_type == "list":
            return weapon_classes
        if data_type == "set":
            return set(weapon_classes)
        return None