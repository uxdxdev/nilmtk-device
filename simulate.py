import utils

building_data = utils.init(1)

fridge_payload = utils.get_payload_for_appliance(building_data, 'fridge')
dishwasher_payload = utils.get_payload_for_appliance(
    building_data, 'dish washer')
washer_dryer_payload = utils.get_payload_for_appliance(
    building_data, 'washer dryer')

utils.check_on_off_states(fridge_payload)
utils.check_on_off_states(dishwasher_payload)
utils.check_on_off_states(washer_dryer_payload)
