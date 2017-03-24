import zoe_lib.config as config
import zoe_api.db_init

config.load_configuration()

zoe_api.db_init.init()
