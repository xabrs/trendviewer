from abc import ABC, abstractmethod

class TrendPlugin(ABC):
    @abstractmethod
    def __init__(self, options):
        pass

    @abstractmethod
    def values(self, itemid, datestart, dateend):
        """
        Returns an array of values in the required format.
        @param itemid:
        @param datestart: start datetime string, format "1970-01-01 00:00:00"
        @param dateend: end datetime string, format "1970-01-01 00:00:00"
        @return:
        list of dict
        [{tag: 1, v: 13.45, dt:"1970-01-01 00:00:00", "q": 0},{tag: 1, v: 25.56, dt:"1970-01-01 00:00:01", "q": 0},]
        """
        pass

    @abstractmethod
    def tree_xml(self):
        """
        @return:
        Returns XML tag list for tree view
        <tree name="module"><Group name="File 1">.
            <Tag tag="56" name="Outdoor temp,C" title="Some text, &#10; second line"/>
        </Group></tree>
        """
        pass