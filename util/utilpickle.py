import pickle
import os


class UtilPickle:
    @staticmethod
    def dump(obj, fileName="dat"):
        dumpFile = os.path.join(os.getcwd(), fileName)
        with open(dumpFile, "wb") as f:
            pickle.dump(obj, f, 0)

    @staticmethod
    def load(fileName="dat"):
        obj = None
        dumpFile = os.path.join(os.getcwd(), fileName)

        if not os.path.exists(dumpFile):
            return obj

        with open(dumpFile, "rb") as f:
            obj = pickle.load(f)
        return obj
