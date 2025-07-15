STRING_LEN = 64
PASSWORD_LEN = 128
NAME_LEN_MIN = 4
NAME_LEN_MAX = 25
PASSWORD_LEN_MIN = 6
PASSWORD_LEN_MAX = 16

STATUS_CLASS = {
    "PENDING": "bg-secondary text-light",
    "RUNNING": "bg-info text-white",
    "SUSPENDED": "bg-warning text-dark",
    "COMPLETED": "bg-success text-white",
    "CANCELLED": "bg-dark text-white",
    "FAILED": "bg-danger text-white",
    "TIMEOUT": "bg-info text-dark",
    "NODE_FAIL": "bg-light text-dark",
    "PREEMPTED": "bg-primary text-white",
    "SPECIAL_EXIT": "bg-secondary text-light",
    "NO_JOB_STATUS": "bg-dark text-white",
}

# Column mappings for sample metadata
SAMPLE_COLUMNS_MAP = {
    1: "name",
    2: "title",
    3: "library",
    4: "organism",
    5: "tissue",
    6: "cell_line",
    7: "cell_type",
    8: "genotype",
    9: "treatment",
    10: "batch",
    11: "molecule",
    12: "single_or_pairedend",
    13: "instrument_model",
    14: "description",
    15: "processed_file_1",
    16: "processed_file_2",
    17: "raw_file_1",
    18: "raw_file_2",
    19: "raw_file_3",
    20: "raw_file_4",
}

# Reverse mapping for easy column lookup
SAMPLE_NAME_TO_COLUMNS = {v: k for k, v in SAMPLE_COLUMNS_MAP.items()}

# Paired-end file columns
PAIREDEND_NAME_TO_COLUMNS = {
    "filename_1": 1,
    "filename_2": 2,
    "filename_3": 3,
    "filename_4": 4,
}

# Sample() attribute mappings
SAMPLE_ATTRIBUTE_COLUMN_MAPPINGS = {
    "name": "name",
    "organism": "organism",
    "instrument": "instrument_model",
}


# no header
# used to know from where to start saving the spreadsheet
# used to know from where relatively to insert/delete rows related to study
# metadata_study_startrow = 11 (OLD)
metadata_study_startrow = 12

# including header
# metadata_samples_startrow = 33 (OLD)
METADATA_SAMPLES_STARTROW = 38

metadata_protocols_instructions = 54
# no header
# metadata_protocols_startrow = 56 (OLD)
metadata_protocols_startrow = 57

# including header
# metadata_pairedend_startrow = 75 (OLD)
METADATA_PAIREDEND_STARTROW = 76

# where to insert a new column when user wants to add more sample data
metadata_samples_column_insert = (
    6  # starting from six on you can insert a column, but until when?
)
metadata_samples_column_raw = 17

metadata_samples_column = 20

MD5_CHECKSUM_STARTROW = 9
