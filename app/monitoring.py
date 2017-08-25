from prometheus_client import Gauge, Counter

FLASK_INPROGRESS_LIFECYCLE = Gauge("flask_inprogress_requests_lifecycle", "Gauge in progress requests",
                                   multiprocess_mode='livesum')
FLASK_NUM_REQUESTS_LIFECYCLE = Counter("flask_num_requests_lifecycle", "Counter of number of requests")

FLASK_INPROGRESS_HEALTHZ = Gauge("flask_inprogress_requests_healthz", "Gauge in progress requests",
                                 multiprocess_mode='livesum')
FLASK_NUM_REQUESTS_HEALTHZ = Counter("flask_num_requests_healthz", "Counter of number of requests")

FLASK_INPROGRESS_DISCOVERY = Gauge("flask_inprogress_requests_discovery", "Gauge in progress requests",
                                   multiprocess_mode='livesum')
FLASK_NUM_REQUESTS_DISCOVERY = Counter("flask_num_requests_discovery", "Counter of number of requests")

FLASK_INPROGRESS_MATCHBOX = Gauge("flask_inprogress_requests_matchbox", "Gauge in progress requests",
                                  multiprocess_mode='livesum')
FLASK_NUM_REQUESTS_MATCHBOX = Counter("flask_num_requests_matchbox", "Counter of number of requests")

FLASK_INPROGRESS_SCHEDULER = Gauge("flask_inprogress_requests_scheduler", "Gauge in progress requests",
                                   multiprocess_mode='livesum')
FLASK_NUM_REQUESTS_SCHEDULER = Counter("flask_num_requests_scheduler", "Counter of number of requests")

FLASK_NUM_REQUESTS_INSTALL_AUTHORIZATION = Counter("flask_num_requests_authorization", "Counter of number of requests")

FLASK_NUM_500 = Counter("flask_num_500", "Counter of number of requests")

SMARTDB_NUM_RETRY = Counter("db_num_retry", "Counter of number of retry in db")
SMARTDB_NUM_CONN_ERROR = Counter("db_num_conn_error", "Counter of number of retry in db")
SMARTDB_NUM_TRANSACTION = Counter("db_num_transaction", "Counter of number of transaction in db")
