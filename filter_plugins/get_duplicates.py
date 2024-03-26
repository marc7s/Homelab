#!/usr/bin/python

class FilterModule(object):
    def filters(self):
        return {'get_duplicates': self.get_duplicates}

    def get_duplicates(self, items):
        counts = {}
        duplicates = []

        for item in items:
            if item not in counts:
                counts[item] = 1
            else:
                if counts[item] == 1:
                    duplicates.append(item)
                counts[item] += 1
        
        return duplicates