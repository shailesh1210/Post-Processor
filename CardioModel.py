from CardioIO import CardioIO


class CardioModel:
    def __init__(self, interface):
        self.__io = CardioIO(interface)

    def import_risk_factor(self, mean_risk_path):
        self.__io.read_risk_factors_data(mean_risk_path)

    def import_total_chd(self, total_chd_path):
        self.__io.read_total_chd_risk(total_chd_path)

    def import_fatal_chd(self, fatal_chd_path):
        self.__io.read_fatal_chd_risk(fatal_chd_path)

    def import_statins_use(self, statins_use_path):
        self.__io.read_statins_use(statins_use_path)

    def output(self):
        self.__io.output()


