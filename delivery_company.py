
class BaseDeliveryCompany:
    """ Parent class """

    def de_at_pl_one_place_delivery_cost(self):
        raise NotImplementedError()

    def fr_be_it_one_place_delivery_cost(self):
        raise NotImplementedError()

    def count_of_tires(self, value):
        return 1


class DPDDeliveryCompany(BaseDeliveryCompany):

    def de_at_pl_one_place_delivery_cost(self):
        return 330

    def fr_be_it_one_place_delivery_cost(self):
        return 400

    def count_of_tires(self, value):
        if value == 1:
            return 1
        if value == 2:
            return 2


class SchenkerDeliveryCompany(BaseDeliveryCompany):

    def de_at_pl_one_place_delivery_cost(self):
        return 2300

    def fr_be_it_one_place_delivery_cost(self):
        return 3600

    def count_of_tires(self, value):
        if value == 1:
            return 1
        if value == 2:
            return 2.5


__COMPANY_MAP = {
    1: DPDDeliveryCompany(),
    2: SchenkerDeliveryCompany(),
}


def get_delivery_company(value):
    return __COMPANY_MAP.get(value)
